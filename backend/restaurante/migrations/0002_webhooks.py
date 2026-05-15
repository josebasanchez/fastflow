# Generated migration for webhook models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('restaurante', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='WebhookSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField(help_text='URL destino para el webhook')),
                ('event_type', models.CharField(choices=[('stock_bajo', 'Stock Bajo'), ('pedido_completado', 'Pedido Completado'), ('pedido_cancelado', 'Pedido Cancelado'), ('nueva_valoracion', 'Nueva Valoración'), ('reserva_confirmada', 'Reserva Confirmada'), ('alerta_ingrediente', 'Alerta de Ingrediente')], max_length=30)),
                ('is_active', models.BooleanField(default=True)),
                ('secret_token', models.CharField(max_length=255, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='webhook_subscriptions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Webhook Subscription',
                'verbose_name_plural': 'Webhook Subscriptions',
                'unique_together': {('user', 'url', 'event_type')},
            },
        ),
        migrations.CreateModel(
            name='WebhookEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(max_length=30)),
                ('payload', models.JSONField(help_text='Datos del evento')),
                ('status', models.CharField(choices=[('pending', 'Pendiente'), ('sent', 'Enviado'), ('failed', 'Fallido'), ('delivered', 'Entregado')], default='pending', max_length=20)),
                ('attempt_count', models.IntegerField(default=0)),
                ('last_attempt_at', models.DateTimeField(blank=True, null=True)),
                ('next_retry_at', models.DateTimeField(blank=True, null=True)),
                ('response_status_code', models.IntegerField(blank=True, null=True)),
                ('response_body', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('subscription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='restaurante.webhooksubscription')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='WebhookDeliveryLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attempt_number', models.IntegerField()),
                ('status_code', models.IntegerField(blank=True, null=True)),
                ('response_time_ms', models.IntegerField(help_text='Tiempo de respuesta en milisegundos')),
                ('error_message', models.TextField(blank=True)),
                ('headers_sent', models.JSONField()),
                ('response_headers', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='delivery_logs', to='restaurante.webhookevent')),
            ],
            options={
                'ordering': ['-created_at'],
                'verbose_name_plural': 'Webhook Delivery Logs',
            },
        ),
        migrations.AddIndex(
            model_name='webhookevent',
            index=models.Index(fields=['status', 'next_retry_at'], name='restaurante_status_next_idx'),
        ),
        migrations.AddIndex(
            model_name='webhookevent',
            index=models.Index(fields=['created_at'], name='restaurante_created_idx'),
        ),
    ]
