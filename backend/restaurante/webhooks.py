"""
Gestor de Webhooks para FastFlow
Envío y manejo de webhooks para eventos del sistema
"""

import requests
import json
import hashlib
import hmac
from typing import Dict, Any, Optional
from datetime import datetime
import threading

from django.utils import timezone
from django.conf import settings

from .webhook_models import WebhookSubscription, WebhookEvent, WebhookDeliveryLog
from .cache_manager import cache_manager


class WebhookManager:
    """Gestor centralizado de webhooks"""
    
    def __init__(self):
        self.timeout = getattr(settings, 'WEBHOOK_TIMEOUT', 10)
        self.max_retries = getattr(settings, 'WEBHOOK_MAX_RETRIES', 5)
    
    @staticmethod
    def generate_signature(payload: str, secret: str) -> str:
        """Generar firma HMAC-SHA256"""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def trigger_event(self, event_type: str, data: Dict[str, Any], async_send: bool = True):
        """
        Disparar evento de webhook
        
        Args:
            event_type: tipo de evento
            data: datos del evento
            async_send: si True, envía en background
        """
        # Obtener suscripciones activas para este evento
        subscriptions = WebhookSubscription.objects.filter(
            event_type=event_type,
            is_active=True
        )
        
        for subscription in subscriptions:
            # Crear evento
            event = WebhookEvent.objects.create(
                subscription=subscription,
                event_type=event_type,
                payload=data,
                status='pending'
            )
            
            # Enviar
            if async_send:
                # En background
                thread = threading.Thread(
                    target=self.send_webhook,
                    args=(event.id,),
                    daemon=True
                )
                thread.start()
            else:
                # Síncrono
                self.send_webhook(event.id)
    
    def send_webhook(self, event_id: int, attempt: int = 1):
        """
        Enviar webhook
        
        Args:
            event_id: ID del evento
            attempt: número de intento
        """
        try:
            event = WebhookEvent.objects.get(id=event_id)
            
            if not event.should_retry():
                if attempt > 1:
                    event.status = 'failed'
                    event.save()
                return
            
            # Preparar payload
            payload = json.dumps({
                'event_type': event.event_type,
                'timestamp': timezone.now().isoformat(),
                'data': event.payload
            })
            
            # Generar firma
            signature = self.generate_signature(
                payload,
                event.subscription.secret_token
            )
            
            # Headers
            headers = {
                'Content-Type': 'application/json',
                'X-Webhook-Signature': signature,
                'X-Webhook-Event': event.event_type,
                'User-Agent': 'FastFlow-Webhook/1.0'
            }
            
            # Enviar
            start_time = datetime.now()
            response = requests.post(
                event.subscription.url,
                data=payload,
                headers=headers,
                timeout=self.timeout
            )
            response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Registrar log
            WebhookDeliveryLog.objects.create(
                event=event,
                attempt_number=attempt,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                headers_sent=headers,
                response_headers=dict(response.headers)
            )
            
            # Actualizar evento
            event.attempt_count = attempt
            event.last_attempt_at = timezone.now()
            event.response_status_code = response.status_code
            event.response_body = response.text[:1000]  # Limitar
            
            # Verificar si fue exitoso
            if response.status_code >= 200 and response.status_code < 300:
                event.status = 'delivered'
                event.save()
            else:
                # Reintentar
                if attempt < self.max_retries:
                    event.status = 'failed'
                    event.calculate_next_retry()
                    event.save()
                else:
                    event.status = 'failed'
                    event.save()
        
        except requests.exceptions.Timeout:
            self._handle_webhook_error(event_id, attempt, "Timeout")
        except requests.exceptions.ConnectionError:
            self._handle_webhook_error(event_id, attempt, "Connection Error")
        except Exception as e:
            self._handle_webhook_error(event_id, attempt, str(e))
    
    def _handle_webhook_error(self, event_id: int, attempt: int, error: str):
        """Manejar error en webhook"""
        try:
            event = WebhookEvent.objects.get(id=event_id)
            
            WebhookDeliveryLog.objects.create(
                event=event,
                attempt_number=attempt,
                error_message=error,
                response_time_ms=0,
                headers_sent={}
            )
            
            event.attempt_count = attempt
            event.last_attempt_at = timezone.now()
            
            if attempt < self.max_retries:
                event.status = 'failed'
                event.calculate_next_retry()
            else:
                event.status = 'failed'
            
            event.save()
        except WebhookEvent.DoesNotExist:
            pass
    
    def retry_pending_webhooks(self):
        """Reintentar webhooks pendientes/fallidos"""
        pending_events = WebhookEvent.objects.filter(
            status__in=['pending', 'failed'],
            next_retry_at__lte=timezone.now()
        )[:100]  # Procesar en lotes
        
        for event in pending_events:
            self.send_webhook(event.id, event.attempt_count + 1)
    
    def get_webhook_stats(self, user_id: int) -> Dict[str, Any]:
        """Obtener estadísticas de webhooks del usuario"""
        subscriptions = WebhookSubscription.objects.filter(user_id=user_id)
        
        stats = {
            'total_subscriptions': subscriptions.count(),
            'active_subscriptions': subscriptions.filter(is_active=True).count(),
            'events': {}
        }
        
        for event_type in dict(WebhookSubscription.EVENT_TYPES).keys():
            events = WebhookEvent.objects.filter(
                subscription__user_id=user_id,
                event_type=event_type
            )
            
            stats['events'][event_type] = {
                'total': events.count(),
                'delivered': events.filter(status='delivered').count(),
                'failed': events.filter(status='failed').count(),
                'pending': events.filter(status='pending').count(),
            }
        
        return stats


# Instancia global
webhook_manager = WebhookManager()
