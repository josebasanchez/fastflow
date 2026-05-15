"""
Modelos para el sistema de Webhooks
"""

from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone


class WebhookSubscription(models.Model):
    """Suscripción a eventos mediante webhook"""
    
    EVENT_TYPES = (
        ('stock_bajo', 'Stock Bajo'),
        ('pedido_completado', 'Pedido Completado'),
        ('pedido_cancelado', 'Pedido Cancelado'),
        ('nueva_valoracion', 'Nueva Valoración'),
        ('reserva_confirmada', 'Reserva Confirmada'),
        ('alerta_ingrediente', 'Alerta de Ingrediente'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='webhook_subscriptions')
    url = models.URLField(help_text="URL destino para el webhook")
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    is_active = models.BooleanField(default=True)
    secret_token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'url', 'event_type')
        verbose_name = 'Webhook Subscription'
        verbose_name_plural = 'Webhook Subscriptions'
    
    def __str__(self):
        return f"{self.user.username} - {self.event_type}"


class WebhookEvent(models.Model):
    """Evento registrado para envío de webhook"""
    
    STATUS_CHOICES = (
        ('pending', 'Pendiente'),
        ('sent', 'Enviado'),
        ('failed', 'Fallido'),
        ('delivered', 'Entregado'),
    )
    
    subscription = models.ForeignKey(WebhookSubscription, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=30)
    payload = models.JSONField(help_text="Datos del evento")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    attempt_count = models.IntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    response_status_code = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'next_retry_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.status}"
    
    def calculate_next_retry(self):
        """Calcular próximo intento (exponential backoff)"""
        # Backoff exponencial: 5min, 15min, 1h, 4h, 24h
        backoff_times = [300, 900, 3600, 14400, 86400]
        delay = backoff_times[min(self.attempt_count, len(backoff_times) - 1)]
        self.next_retry_at = timezone.now() + timedelta(seconds=delay)
    
    def should_retry(self) -> bool:
        """Verificar si debe reintentar"""
        max_attempts = 5
        if self.attempt_count >= max_attempts:
            return False
        if self.next_retry_at and self.next_retry_at > timezone.now():
            return False
        return self.status in ['pending', 'failed']


class WebhookDeliveryLog(models.Model):
    """Log detallado de intentos de entrega"""
    
    event = models.ForeignKey(WebhookEvent, on_delete=models.CASCADE, related_name='delivery_logs')
    attempt_number = models.IntegerField()
    status_code = models.IntegerField(null=True, blank=True)
    response_time_ms = models.IntegerField(help_text="Tiempo de respuesta en milisegundos")
    error_message = models.TextField(blank=True)
    headers_sent = models.JSONField()
    response_headers = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Webhook Delivery Logs'
    
    def __str__(self):
        return f"Attempt {self.attempt_number} - Event {self.event_id}"
