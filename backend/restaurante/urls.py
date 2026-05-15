from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .views import (
    comentarios_plato_view,
    cliente_updates_stream_view,
    dashboard_stats_view,
    IngredienteViewSet,
    MesaViewSet,
    PedidoViewSet,
    PlatoViewSet,
    RecetaViewSet,
    ReservaViewSet,
    UsuarioViewSet,
    login_view,
    me_view,
    dias_completos_por_capacidad_view,
    mesa_horas_ocupadas_view,
    mesas_disponibles_view,
    platos_publicos_view,
    private_updates_stream_view,
    profile_view,
    register_view,
    reserva_cliente_view,
    set_theme_view,
    valoraciones_plato_view,
    voto_comentario_view,
)

from .webhook_views import (
    webhook_subscriptions_view,
    webhook_subscription_detail_view,
    webhook_test_view,
)

router = DefaultRouter()
router.register(r"mesas", MesaViewSet)
router.register(r"reservas", ReservaViewSet)
router.register(r"pedidos", PedidoViewSet)
router.register(r"usuarios", UsuarioViewSet)
router.register(r"ingredientes", IngredienteViewSet)
router.register(r"platos", PlatoViewSet)
router.register(r"recetas", RecetaViewSet)

urlpatterns = [
    path("auth/login/", login_view),
    path("auth/register/", register_view),
    path("auth/token/refresh/", TokenRefreshView.as_view()),
    path("auth/token/verify/", TokenVerifyView.as_view()),
    path("auth/me/", me_view),
    path("auth/profile/", profile_view),
    path("auth/theme/", set_theme_view),
    path("admin/dashboard-stats/", dashboard_stats_view),
    path("stream/private-updates/", private_updates_stream_view),
    path("stream/cliente-updates/", cliente_updates_stream_view),
    path("cliente/mesas-disponibles/", mesas_disponibles_view),
    path("cliente/mesas/<int:mesa_id>/horas-ocupadas/", mesa_horas_ocupadas_view),
    path("cliente/mesas/dias-completos/", dias_completos_por_capacidad_view),
    path("cliente/platos/", platos_publicos_view),
    path("cliente/platos/<int:plato_id>/valoraciones/", valoraciones_plato_view),
    path("cliente/platos/<int:plato_id>/comentarios/", comentarios_plato_view),
    path("cliente/comentarios/<int:comentario_id>/voto/", voto_comentario_view),
    path("cliente/reserva/", reserva_cliente_view),
    # Webhooks
    path("webhooks/subscriptions/", webhook_subscriptions_view),
    path("webhooks/subscriptions/<int:webhook_id>/", webhook_subscription_detail_view),
    path("webhooks/test/", webhook_test_view),
    path("", include(router.urls)),
]
