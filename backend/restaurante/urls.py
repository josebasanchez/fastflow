from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MesaViewSet, ReservaViewSet, PedidoViewSet, UsuarioViewSet

router = DefaultRouter()
router.register(r'mesas', MesaViewSet)
router.register(r'reservas', ReservaViewSet)
router.register(r'pedidos', PedidoViewSet)
router.register(r'usuarios', UsuarioViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
