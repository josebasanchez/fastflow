"""
Webhook Views para FastFlow
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .webhooks import webhook_manager
from .webhook_models import WebhookSubscription, WebhookEvent


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def webhook_subscriptions_view(request):
    """Gestionar suscripciones a webhooks"""
    
    if request.method == 'GET':
        # Listar suscripciones del usuario
        subs = WebhookSubscription.objects.filter(user=request.user)
        data = [
            {
                'id': sub.id,
                'url': sub.url,
                'event_type': sub.event_type,
                'is_active': sub.is_active,
                'created_at': sub.created_at.isoformat()
            }
            for sub in subs
        ]
        return Response(data)
    
    elif request.method == 'POST':
        # Crear nueva suscripción
        try:
            url = request.data.get('url')
            event_type = request.data.get('event_type')
            
            if not url or not event_type:
                return Response(
                    {'error': 'URL y event_type son requeridos'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Generar token secreto
            import secrets
            secret = secrets.token_urlsafe(32)
            
            sub = WebhookSubscription.objects.create(
                user=request.user,
                url=url,
                event_type=event_type,
                secret_token=secret
            )
            
            return Response({
                'id': sub.id,
                'url': sub.url,
                'event_type': sub.event_type,
                'secret_token': secret,
                'created_at': sub.created_at.isoformat()
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def webhook_subscription_detail_view(request, webhook_id):
    """Detalle de suscripción de webhook"""
    
    try:
        sub = WebhookSubscription.objects.get(id=webhook_id, user=request.user)
    except WebhookSubscription.DoesNotExist:
        return Response(
            {'error': 'Webhook no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        return Response({
            'id': sub.id,
            'url': sub.url,
            'event_type': sub.event_type,
            'is_active': sub.is_active,
            'created_at': sub.created_at.isoformat()
        })
    
    elif request.method == 'DELETE':
        sub.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def webhook_subscription_toggle_view(request, webhook_id):
    """Activar/desactivar suscripción"""
    
    try:
        sub = WebhookSubscription.objects.get(id=webhook_id, user=request.user)
    except WebhookSubscription.DoesNotExist:
        return Response(
            {'error': 'Webhook no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    sub.is_active = request.data.get('is_active', sub.is_active)
    sub.save()
    
    return Response({
        'id': sub.id,
        'is_active': sub.is_active
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def webhook_events_view(request):
    """Listar eventos de webhook"""
    
    try:
        sub_id = request.query_params.get('subscription_id')
        status_filter = request.query_params.get('status')
        
        query = WebhookEvent.objects.filter(subscription__user=request.user)
        
        if sub_id:
            query = query.filter(subscription_id=sub_id)
        
        if status_filter:
            query = query.filter(status=status_filter)
        
        events = query.order_by('-created_at')[:100]
        
        data = [
            {
                'id': event.id,
                'event_type': event.event_type,
                'status': event.status,
                'attempt_count': event.attempt_count,
                'created_at': event.created_at.isoformat(),
                'last_attempt_at': event.last_attempt_at.isoformat() if event.last_attempt_at else None
            }
            for event in events
        ]
        
        return Response(data)
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def webhook_stats_view(request):
    """Obtener estadísticas de webhooks"""
    
    stats = webhook_manager.get_webhook_stats(request.user.id)
    return Response(stats)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def webhook_retry_view(request):
    """Reintentar evento de webhook"""
    
    try:
        event_id = request.data.get('event_id')
        
        try:
            event = WebhookEvent.objects.get(
                id=event_id,
                subscription__user=request.user
            )
        except WebhookEvent.DoesNotExist:
            return Response(
                {'error': 'Evento no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Reintentar
        webhook_manager.send_webhook(event.id, event.attempt_count + 1)
        
        return Response({
            'status': 'retry_initiated',
            'event_id': event_id
        })
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def webhook_test_view(request):
    """Enviar webhook de prueba"""
    
    try:
        webhook_id = request.data.get('webhook_id')
        
        try:
            subscription = WebhookSubscription.objects.get(
                id=webhook_id,
                user=request.user
            )
        except WebhookSubscription.DoesNotExist:
            return Response(
                {'error': 'Webhook no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Crear evento de prueba
        test_data = {
            'test': True,
            'timestamp': str(__import__('django.utils.timezone', fromlist=['now']).now()),
            'message': 'Este es un webhook de prueba'
        }
        
        event = WebhookEvent.objects.create(
            subscription=subscription,
            event_type=subscription.event_type,
            payload=test_data,
            status='pending'
        )
        
        # Enviar inmediatamente
        webhook_manager.send_webhook(event.id)
        
        return Response({
            'status': 'test_sent',
            'event_id': event.id,
            'webhook_id': webhook_id
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
