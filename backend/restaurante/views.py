import json
import time
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Count, F, Sum
from django.db.models.functions import TruncDate
from django.db import close_old_connections, transaction
from django.http import JsonResponse, StreamingHttpResponse
from django.utils import timezone
from django.views.decorators.http import require_GET
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from .models import ComentarioPlato, Ingrediente, Mesa, Pago, Pedido, PerfilUsuario, Plato, Receta, Reserva, ValoracionPlato, VotoComentario
from .permissions import IsAdminOnly, IsAdminOrEmpleado, IsAdminOrReadOnly
from .serializers import (
    ComentarioPlatoSerializer,
    IngredienteSerializer,
    MesaSerializer,
    PagoSerializer,
    PerfilUpdateSerializer,
    PedidoSerializer,
    ReservaClienteSerializer,
    PlatoSerializer,
    RecetaSerializer,
    ReservaSerializer,
    UsuarioSerializer,
    ValoracionPlatoSerializer,
)

RESERVA_DURACION_MINUTOS = 60
SLOTS_SERVICIO = [
    "14:00", "14:15", "14:30", "14:45", "15:00", "15:15", "15:30", "15:45", "16:00",
    "20:00", "20:15", "20:30", "20:45", "21:00", "21:15", "21:30", "21:45", "22:00", "22:15", "22:30",
]


def _reserva_solapa(mesa, fecha, hora):
    inicio = datetime.combine(fecha, hora)
    fin = inicio + timedelta(minutes=RESERVA_DURACION_MINUTOS)
    existentes = Reserva.objects.filter(mesa=mesa, fecha=fecha).exclude(estado=Reserva.ESTADO_CANCELADA)
    for reserva in existentes:
        inicio_existente = datetime.combine(reserva.fecha, reserva.hora)
        fin_existente = inicio_existente + timedelta(minutes=RESERVA_DURACION_MINUTOS)
        if inicio < fin_existente and inicio_existente < fin:
            return True
    return False


def _build_dashboard_stats_payload():
    total_reservas = Reserva.objects.count()
    reservas_hoy = Reserva.objects.filter(fecha=timezone.localdate()).count()
    pedidos_abiertos = Pedido.objects.exclude(estado=Pedido.ESTADO_ENTREGADO).count()
    pedidos_entregados = Pedido.objects.filter(estado=Pedido.ESTADO_ENTREGADO).count()
    ingresos_totales = Pago.objects.filter(estado=Pago.ESTADO_APROBADO).aggregate(total=Sum("importe"))["total"] or Decimal("0")
    alertas_stock = Ingrediente.objects.filter(stock_actual__lte=F("umbral_alerta")).count()
    top_platos = (
        Pedido.objects.values("plato_texto")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )
    hoy = timezone.localdate()
    inicio = hoy - timedelta(days=13)

    reservas_historico_qs = (
        Reserva.objects.filter(fecha__gte=inicio, fecha__lte=hoy)
        .values("fecha")
        .annotate(total=Count("id"))
    )
    reservas_por_dia = {row["fecha"].strftime("%Y-%m-%d"): row["total"] for row in reservas_historico_qs}

    ingresos_historico_qs = (
        Pago.objects.filter(estado=Pago.ESTADO_APROBADO, creado_en__date__gte=inicio, creado_en__date__lte=hoy)
        .annotate(dia=TruncDate("creado_en"))
        .values("dia")
        .annotate(total=Sum("importe"))
    )
    ingresos_por_dia = {row["dia"].strftime("%Y-%m-%d"): str(row["total"] or Decimal("0")) for row in ingresos_historico_qs}

    pedidos_historico_qs = (
        Pedido.objects.filter(creado_en__date__gte=inicio, creado_en__date__lte=hoy)
        .annotate(dia=TruncDate("creado_en"))
        .values("dia")
        .annotate(total=Count("id"))
    )
    pedidos_por_dia = {row["dia"].strftime("%Y-%m-%d"): row["total"] for row in pedidos_historico_qs}

    labels_14d = [(inicio + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(14)]
    reservas_historico = [{"fecha": d, "total": reservas_por_dia.get(d, 0)} for d in labels_14d]
    ingresos_historico = [{"fecha": d, "total": ingresos_por_dia.get(d, "0")} for d in labels_14d]
    pedidos_historico = [{"fecha": d, "total": pedidos_por_dia.get(d, 0)} for d in labels_14d]

    pedidos_por_estado = (
        Pedido.objects.values("estado")
        .annotate(total=Count("id"))
        .order_by("estado")
    )
    empleados_productividad_qs = (
        Pedido.objects.filter(
            preparado_por__isnull=False,
            preparado_en__date__gte=inicio,
            preparado_en__date__lte=hoy,
        )
        .annotate(dia=TruncDate("preparado_en"))
        .values("dia", "preparado_por__username", "preparado_por__first_name")
        .annotate(total_platos=Sum("cantidad"))
        .order_by("dia", "-total_platos", "preparado_por__username")
    )
    top_empleado_por_dia_map = {}
    for row in empleados_productividad_qs:
        day_key = row["dia"].strftime("%Y-%m-%d")
        if day_key not in top_empleado_por_dia_map:
            nombre = row["preparado_por__first_name"] or row["preparado_por__username"]
            top_empleado_por_dia_map[day_key] = {
                "fecha": day_key,
                "empleado": nombre,
                "username": row["preparado_por__username"],
                "platos": int(row["total_platos"] or 0),
            }
    top_empleado_por_dia_14d = [
        top_empleado_por_dia_map.get(
            d,
            {"fecha": d, "empleado": "-", "username": "", "platos": 0},
        )
        for d in labels_14d
    ]

    ranking_empleados_14d_qs = (
        Pedido.objects.filter(
            preparado_por__isnull=False,
            preparado_en__date__gte=inicio,
            preparado_en__date__lte=hoy,
        )
        .values("preparado_por__username", "preparado_por__first_name")
        .annotate(total_platos=Sum("cantidad"))
        .order_by("-total_platos", "preparado_por__username")[:10]
    )
    ranking_empleados_14d = [
        {
            "empleado": row["preparado_por__first_name"] or row["preparado_por__username"],
            "username": row["preparado_por__username"],
            "platos": int(row["total_platos"] or 0),
        }
        for row in ranking_empleados_14d_qs
    ]

    pedidos_preparados = Pedido.objects.filter(preparado_en__isnull=False, listo_en__isnull=False).only("preparado_en", "listo_en")
    duraciones_seg = [int((p.listo_en - p.preparado_en).total_seconds()) for p in pedidos_preparados if p.listo_en and p.preparado_en and p.listo_en >= p.preparado_en]
    tiempo_medio_preparacion_seg = int(sum(duraciones_seg) / len(duraciones_seg)) if duraciones_seg else None

    return {
        "total_reservas": total_reservas,
        "reservas_hoy": reservas_hoy,
        "pedidos_abiertos": pedidos_abiertos,
        "pedidos_entregados": pedidos_entregados,
        "ingresos_totales": str(ingresos_totales),
        "alertas_stock": alertas_stock,
        "top_platos": list(top_platos),
        "reservas_historico_14d": reservas_historico,
        "ingresos_historico_14d": ingresos_historico,
        "pedidos_historico_14d": pedidos_historico,
        "pedidos_por_estado": list(pedidos_por_estado),
        "top_empleado_por_dia_14d": top_empleado_por_dia_14d,
        "ranking_empleados_14d": ranking_empleados_14d,
        "tiempo_medio_preparacion_segundos": tiempo_medio_preparacion_seg,
    }


def _authenticate_stream_user(request):
    auth = request.META.get("HTTP_AUTHORIZATION", "")
    if auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1].strip()
    else:
        token = request.GET.get("token", "").strip()
    if not token:
        return None
    try:
        jwt_auth = JWTAuthentication()
        validated_token = jwt_auth.get_validated_token(token)
        user = jwt_auth.get_user(validated_token)
        return user if user and user.is_active else None
    except Exception:
        return None


@require_GET
def private_updates_stream_view(request):
    user = _authenticate_stream_user(request)
    if not user:
        return JsonResponse({"detail": "Unauthorized"}, status=401)

    perfil = getattr(user, "perfil", None)
    rol = getattr(perfil, "rol", "cliente")
    is_admin = bool(user.is_staff or rol == PerfilUsuario.ROL_ADMIN)
    is_empleado = bool(is_admin or rol == PerfilUsuario.ROL_EMPLEADO)

    def event_stream():
        try:
            while True:
                close_old_connections()
                payload = {
                    "server_time": timezone.now().isoformat(),
                    "rol": rol,
                }
                if is_empleado:
                    pedidos = Pedido.objects.select_related("plato", "reserva", "reserva__mesa", "preparado_por").exclude(estado=Pedido.ESTADO_ENTREGADO).order_by("fecha_limite", "id")
                    payload["pedidos"] = PedidoSerializer(pedidos, many=True).data
                if is_admin:
                    payload["stats"] = _build_dashboard_stats_payload()
                    payload["adminPlatos"] = PlatoSerializer(Plato.objects.all().order_by("nombre"), many=True).data
                    payload["adminIngredientes"] = IngredienteSerializer(Ingrediente.objects.all().order_by("nombre"), many=True).data
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                time.sleep(5)
        except GeneratorExit:
            return

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    response["Access-Control-Allow-Origin"] = "*"
    return response


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get("username", "")
    password = request.data.get("password", "")
    user = authenticate(username=username, password=password)
    if not user:
        return Response({"detail": "Credenciales invalidas"}, status=status.HTTP_401_UNAUTHORIZED)

    refresh = RefreshToken.for_user(user)
    perfil = getattr(user, "perfil", None)
    return Response(
        {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "email": user.email,
                "rol": getattr(perfil, "rol", "cliente"),
                "tema": getattr(perfil, "tema", PerfilUsuario.THEME_LIGHT),
                "idioma": getattr(perfil, "idioma", PerfilUsuario.LANG_ES),
                "nombre_mostrar": getattr(perfil, "nombre_mostrar", "") or user.first_name or user.username,
                "is_staff": user.is_staff,
            },
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    payload = request.data.copy()
    payload["rol"] = PerfilUsuario.ROL_CLIENTE
    serializer = UsuarioSerializer(data=payload)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    refresh = RefreshToken.for_user(user)
    perfil = getattr(user, "perfil", None)
    return Response(
        {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "email": user.email,
                "rol": getattr(perfil, "rol", "cliente"),
                "tema": getattr(perfil, "tema", PerfilUsuario.THEME_LIGHT),
                "idioma": getattr(perfil, "idioma", PerfilUsuario.LANG_ES),
                "nombre_mostrar": getattr(perfil, "nombre_mostrar", "") or user.first_name or user.username,
                "is_staff": user.is_staff,
            },
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_stats_view(request):
    if not request.user.is_staff:
        return Response({"detail": "Solo administradores"}, status=status.HTTP_403_FORBIDDEN)
    return Response(_build_dashboard_stats_payload())


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    user = request.user
    perfil = getattr(user, "perfil", None)
    return Response(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "rol": getattr(perfil, "rol", "cliente"),
            "tema": getattr(perfil, "tema", PerfilUsuario.THEME_LIGHT),
            "idioma": getattr(perfil, "idioma", PerfilUsuario.LANG_ES),
            "nombre_mostrar": getattr(perfil, "nombre_mostrar", ""),
            "telefono": getattr(perfil, "telefono", ""),
            "is_staff": user.is_staff,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def set_theme_view(request):
    tema = request.data.get("tema")
    if tema not in {PerfilUsuario.THEME_LIGHT, PerfilUsuario.THEME_DARK}:
        return Response({"detail": "Tema invalido"}, status=status.HTTP_400_BAD_REQUEST)
    perfil, _ = PerfilUsuario.objects.get_or_create(user=request.user)
    perfil.tema = tema
    perfil.save(update_fields=["tema"])
    return Response({"tema": perfil.tema})


@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def profile_view(request):
    perfil, _ = PerfilUsuario.objects.get_or_create(user=request.user)
    if request.method == "GET":
        return Response(PerfilUpdateSerializer(perfil).data)

    serializer = PerfilUpdateSerializer(perfil, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def mesas_disponibles_view(request):
    fecha = request.query_params.get("fecha")
    hora = request.query_params.get("hora")
    capacidad = request.query_params.get("capacidad")
    disposicion = request.query_params.get("disposicion")
    if not fecha:
        return Response({"detail": "fecha es obligatoria"}, status=status.HTTP_400_BAD_REQUEST)

    qs = Mesa.objects.all().order_by("id")
    if capacidad:
        try:
            qs = qs.filter(capacidad__gte=int(capacidad))
        except ValueError:
            return Response({"detail": "capacidad invalida"}, status=status.HTTP_400_BAD_REQUEST)
    if disposicion:
        qs = qs.filter(disposicion__iexact=disposicion)

    try:
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
    except ValueError:
        return Response({"detail": "fecha invalida"}, status=status.HTTP_400_BAD_REQUEST)

    if hora:
        try:
            hora_obj = datetime.strptime(hora, "%H:%M").time()
        except ValueError:
            return Response({"detail": "hora invalida"}, status=status.HTTP_400_BAD_REQUEST)
        mesas_disponibles = [mesa for mesa in qs if not _reserva_solapa(mesa, fecha_obj, hora_obj)]
        qs = mesas_disponibles

    return Response(MesaSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def mesa_horas_ocupadas_view(request, mesa_id):
    fecha = request.query_params.get("fecha")
    if not fecha:
        return Response({"detail": "fecha es obligatoria"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
    except ValueError:
        return Response({"detail": "fecha invalida"}, status=status.HTTP_400_BAD_REQUEST)

    mesa = Mesa.objects.filter(id=mesa_id).first()
    if not mesa:
        return Response({"detail": "Mesa no encontrada"}, status=status.HTTP_404_NOT_FOUND)

    slots = []
    for slot in SLOTS_SERVICIO:
        hora = datetime.strptime(slot, "%H:%M").time()
        if _reserva_solapa(mesa, fecha_obj, hora):
            slots.append(slot)

    return Response({"mesa_id": mesa.id, "fecha": fecha, "horas_ocupadas": slots})


@api_view(["GET"])
@permission_classes([AllowAny])
def dias_completos_por_capacidad_view(request):
    capacidad = request.query_params.get("capacidad")
    year = request.query_params.get("year")
    month = request.query_params.get("month")
    if not capacidad or not year or not month:
        return Response({"detail": "capacidad, year y month son obligatorios"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        capacidad_int = int(capacidad)
        year_int = int(year)
        month_int = int(month)
    except ValueError:
        return Response({"detail": "parametros invalidos"}, status=status.HTTP_400_BAD_REQUEST)

    if month_int < 1 or month_int > 12:
        return Response({"detail": "month invalido"}, status=status.HTTP_400_BAD_REQUEST)

    if capacidad_int <= 2:
        allowed = {"m1", "mesa1", "m2", "mesa2"}
    elif capacidad_int == 3:
        allowed = {"m3", "mesa3"}
    elif capacidad_int in (4, 5):
        allowed = {"m4", "mesa4", "m5", "mesa5"}
    else:
        allowed = {"m6", "mesa6"}

    def normalize(nombre):
        # Mantener consistente con el frontend: minúsculas, sin espacios y sin caracteres no alfanuméricos.
        return "".join(ch for ch in nombre.lower() if ch.isalnum())

    mesas = [m for m in Mesa.objects.all().order_by("id") if normalize(m.nombre) in allowed]
    if not mesas:
        return Response({"capacidad": capacidad_int, "year": year_int, "month": month_int, "dias_completos": []})

    first_day = datetime(year_int, month_int, 1).date()
    if month_int == 12:
        next_month = datetime(year_int + 1, 1, 1).date()
    else:
        next_month = datetime(year_int, month_int + 1, 1).date()
    total_days = (next_month - first_day).days

    dias_completos = []
    for day in range(1, total_days + 1):
        fecha_obj = first_day.replace(day=day)
        all_group_full = True
        for mesa in mesas:
            mesa_full = True
            for slot in SLOTS_SERVICIO:
                hora = datetime.strptime(slot, "%H:%M").time()
                if not _reserva_solapa(mesa, fecha_obj, hora):
                    mesa_full = False
                    break
            if not mesa_full:
                all_group_full = False
                break
        if all_group_full:
            dias_completos.append(fecha_obj.strftime("%Y-%m-%d"))

    return Response({"capacidad": capacidad_int, "year": year_int, "month": month_int, "dias_completos": dias_completos})


@require_GET
def cliente_updates_stream_view(request):
    fecha = request.GET.get("fecha")
    capacidad = request.GET.get("capacidad")
    if not fecha:
        return JsonResponse({"detail": "fecha es obligatoria"}, status=400)

    try:
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"detail": "fecha invalida"}, status=400)

    capacidad_int = None
    if capacidad:
        try:
            capacidad_int = int(capacidad)
        except ValueError:
            return JsonResponse({"detail": "capacidad invalida"}, status=400)

    def event_stream():
        try:
            while True:
                close_old_connections()
                mesas_qs = Mesa.objects.all().order_by("id")
                if capacidad_int:
                    mesas_qs = mesas_qs.filter(capacidad__gte=capacidad_int)
                mesas = list(mesas_qs)
                mesas_data = MesaSerializer(mesas, many=True).data

                occupied_by_mesa = {}
                for mesa in mesas:
                    slots = []
                    for slot in SLOTS_SERVICIO:
                        hora = datetime.strptime(slot, "%H:%M").time()
                        if _reserva_solapa(mesa, fecha_obj, hora):
                            slots.append(slot)
                    occupied_by_mesa[str(mesa.id)] = slots

                payload = {
                    "server_time": timezone.now().isoformat(),
                    "fecha": fecha,
                    "mesas": mesas_data,
                    "occupied_slots_by_mesa": occupied_by_mesa,
                }
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                time.sleep(5)
        except GeneratorExit:
            return

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    response["Access-Control-Allow-Origin"] = "*"
    return response


@api_view(["GET"])
@permission_classes([AllowAny])
def platos_publicos_view(request):
    platos = Plato.objects.filter(disponible=True).order_by("nombre")
    vegano = request.query_params.get("vegano")
    halal = request.query_params.get("halal")

    if vegano == "true":
        platos = platos.filter(es_vegano=True)
    if halal == "true":
        platos = platos.filter(es_halal=True)

    return Response(PlatoSerializer(platos, many=True, context={"request": request}).data)


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def valoraciones_plato_view(request, plato_id):
    plato = Plato.objects.filter(id=plato_id, disponible=True).first()
    if not plato:
        return Response({"detail": "Plato no encontrado"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        valoraciones = ValoracionPlato.objects.filter(plato=plato).order_by("-creado_en")[:100]
        return Response(ValoracionPlatoSerializer(valoraciones, many=True).data)

    serializer = ValoracionPlatoSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    puntuacion = serializer.validated_data["puntuacion"]
    if puntuacion < 1 or puntuacion > 5:
        return Response({"detail": "La puntuacion debe estar entre 1 y 5"}, status=status.HTTP_400_BAD_REQUEST)

    valoracion, _ = ValoracionPlato.objects.update_or_create(
        plato=plato,
        email_cliente=serializer.validated_data["email_cliente"],
        defaults={"puntuacion": puntuacion},
    )
    return Response(ValoracionPlatoSerializer(valoracion).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def comentarios_plato_view(request, plato_id):
    plato = Plato.objects.filter(id=plato_id, disponible=True).first()
    if not plato:
        return Response({"detail": "Plato no encontrado"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        # Paginación: page (1-based) y page_size (default 5)
        try:
            page = int(request.query_params.get("page", 1))
            page_size = int(request.query_params.get("page_size", 5))
        except ValueError:
            page = 1
            page_size = 5
        
        page = max(1, page)
        page_size = max(1, min(50, page_size))  # Limitar a máximo 50 por página
        
        total = ComentarioPlato.objects.filter(plato=plato).count()
        start = (page - 1) * page_size
        end = start + page_size
        
        comentarios = ComentarioPlato.objects.filter(plato=plato).order_by("-creado_en")[start:end]
        
        return Response({
            "results": ComentarioPlatoSerializer(comentarios, many=True).data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        })

    serializer = ComentarioPlatoSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    comentario = ComentarioPlato.objects.create(
        plato=plato,
        nombre_cliente=serializer.validated_data["nombre_cliente"],
        email_cliente=serializer.validated_data["email_cliente"],
        comentario=serializer.validated_data["comentario"],
    )
    return Response(ComentarioPlatoSerializer(comentario).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def voto_comentario_view(request, comentario_id):
    comentario = ComentarioPlato.objects.filter(id=comentario_id).first()
    if not comentario:
        return Response({"detail": "Comentario no encontrado"}, status=status.HTTP_404_NOT_FOUND)

    email_cliente = request.data.get("email_cliente", "").strip()
    tipo = request.data.get("tipo", "").strip().lower()

    if not email_cliente:
        return Response({"detail": "email_cliente es obligatorio"}, status=status.HTTP_400_BAD_REQUEST)
    if tipo not in {VotoComentario.TIPO_LIKE, VotoComentario.TIPO_DISLIKE}:
        return Response({"detail": "tipo debe ser like o dislike"}, status=status.HTTP_400_BAD_REQUEST)

    VotoComentario.objects.update_or_create(
        comentario=comentario,
        email_cliente=email_cliente,
        defaults={"tipo": tipo},
    )
    return Response(ComentarioPlatoSerializer(comentario).data)


def _simular_pago(metodo, referencia):
    if metodo == Pago.METODO_LOCAL:
        return Pago.ESTADO_PENDIENTE
    ref = (referencia or "").strip()
    if ref and ref[-1].isdigit():
        return Pago.ESTADO_APROBADO if int(ref[-1]) % 2 == 0 else Pago.ESTADO_RECHAZADO
    return Pago.ESTADO_APROBADO


def _descontar_para_preparacion(pedido):
    if not pedido.plato_id or pedido.ingredientes_descontados:
        return
    receta_items = list(pedido.plato.recetas.select_related("ingrediente").all())
    for receta in receta_items:
        requerido = receta.cantidad * Decimal(pedido.cantidad)
        if receta.ingrediente.stock_actual < requerido:
            raise InvalidOperation(f"Stock insuficiente para {receta.ingrediente.nombre}")
    for receta in receta_items:
        requerido = receta.cantidad * Decimal(pedido.cantidad)
        ing = receta.ingrediente
        ing.stock_actual -= requerido
        ing.save(update_fields=["stock_actual"])
    pedido.ingredientes_descontados = True
    pedido.estado = Pedido.ESTADO_LISTO
    pedido.save(update_fields=["ingredientes_descontados", "estado"])


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def reserva_cliente_view(request):
    serializer = ReservaClienteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    mesa = Mesa.objects.filter(id=data["mesa_id"]).first()
    if not mesa:
        return Response({"detail": "Mesa no encontrada"}, status=status.HTTP_404_NOT_FOUND)

    if _reserva_solapa(mesa, data["fecha"], data["hora"]):
        return Response({"detail": "Mesa no disponible para esa fecha/hora"}, status=status.HTTP_400_BAD_REQUEST)

    reserva = Reserva.objects.create(
        mesa=mesa,
        nombre_cliente=data["nombre_cliente"],
        email_cliente=data["email_cliente"],
        fecha=data["fecha"],
        hora=data["hora"],
        estado=Reserva.ESTADO_CONFIRMADA,
        pedido_anticipado=data["pedido_anticipado"],
    )
    mesa.estado = Mesa.ESTADO_RESERVADA
    mesa.save(update_fields=["estado"])

    limite_naive = datetime.combine(data["fecha"], data["hora"]) - timedelta(minutes=30)
    fecha_limite = timezone.make_aware(limite_naive, timezone.get_current_timezone())

    total = Decimal("0")
    pedidos = []
    for item in data["pedidos"]:
        plato = Plato.objects.filter(id=item["plato_id"]).first()
        if not plato:
            return Response({"detail": f"Plato {item['plato_id']} no encontrado"}, status=status.HTTP_400_BAD_REQUEST)
        pedido = Pedido.objects.create(
            reserva=reserva,
            plato=plato,
            plato_texto=plato.nombre,
            cantidad=item["cantidad"],
            precio=plato.precio * Decimal(item["cantidad"]),
            estado=Pedido.ESTADO_PENDIENTE,
            fecha_limite=fecha_limite,
        )
        total += pedido.precio
        pedidos.append(pedido)

    estado_pago = _simular_pago(data["metodo_pago"], data.get("referencia_pago"))
    pago = Pago.objects.create(
        reserva=reserva,
        metodo=data["metodo_pago"],
        estado=estado_pago,
        referencia=data.get("referencia_pago", ""),
        importe=total,
    )

    if estado_pago == Pago.ESTADO_APROBADO and data["pedido_anticipado"]:
        for pedido in pedidos:
            _descontar_para_preparacion(pedido)

    return Response({"reserva": ReservaSerializer(reserva).data, "pedidos": PedidoSerializer(pedidos, many=True).data, "pago": PagoSerializer(pago).data}, status=status.HTTP_201_CREATED)


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = User.objects.select_related("perfil").all().order_by("id")
    serializer_class = UsuarioSerializer
    permission_classes = [IsAdminOnly]


class MesaViewSet(viewsets.ModelViewSet):
    queryset = Mesa.objects.all().order_by("id")
    serializer_class = MesaSerializer
    permission_classes = [IsAdminOrEmpleado]


class ReservaViewSet(viewsets.ModelViewSet):
    queryset = Reserva.objects.all().order_by("-fecha", "-hora")
    serializer_class = ReservaSerializer
    permission_classes = [IsAdminOrEmpleado]


class IngredienteViewSet(viewsets.ModelViewSet):
    queryset = Ingrediente.objects.all().order_by("nombre")
    serializer_class = IngredienteSerializer
    permission_classes = [IsAdminOrReadOnly]

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOnly])
    def reponer(self, request, pk=None):
        ingrediente = self.get_object()
        cantidad = request.data.get("cantidad")
        try:
            cantidad = Decimal(str(cantidad))
        except (TypeError, ValueError, InvalidOperation):
            return Response({"detail": "Cantidad invalida"}, status=status.HTTP_400_BAD_REQUEST)
        if cantidad <= 0:
            return Response({"detail": "La cantidad debe ser mayor que 0"}, status=status.HTTP_400_BAD_REQUEST)
        ingrediente.stock_actual = ingrediente.stock_actual + cantidad
        ingrediente.save(update_fields=["stock_actual"])
        return Response(self.get_serializer(ingrediente).data)


class PlatoViewSet(viewsets.ModelViewSet):
    queryset = Plato.objects.all().order_by("nombre")
    serializer_class = PlatoSerializer
    permission_classes = [IsAdminOrReadOnly]

    @action(detail=True, methods=["get"])
    def disponibilidad(self, request, pk=None):
        plato = self.get_object()
        try:
            cantidad = int(request.query_params.get("cantidad", 1))
        except ValueError:
            cantidad = 1
        return Response({"plato_id": plato.id, "cantidad": cantidad, "puede_prepararse": plato.puede_prepararse(cantidad=max(cantidad, 1))})


class RecetaViewSet(viewsets.ModelViewSet):
    queryset = Receta.objects.select_related("plato", "ingrediente").all().order_by("plato_id")
    serializer_class = RecetaSerializer
    permission_classes = [IsAdminOnly]


class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.select_related("plato", "reserva", "reserva__mesa", "preparado_por").all().order_by("fecha_limite", "-creado_en")
    serializer_class = PedidoSerializer
    permission_classes = [IsAdminOrEmpleado]

    @action(detail=False, methods=["get"])
    def en_directo(self, request):
        pedidos = self.queryset.exclude(estado=Pedido.ESTADO_ENTREGADO)[:30]
        serializer = self.get_serializer(pedidos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def cola_preparacion(self, request):
        pedidos = self.queryset.exclude(estado=Pedido.ESTADO_ENTREGADO).order_by("fecha_limite", "id")
        return Response(self.get_serializer(pedidos, many=True).data)

    @action(detail=True, methods=["post"])
    def iniciar_preparacion(self, request, pk=None):
        pedido = self.get_object()
        if pedido.estado in {Pedido.ESTADO_LISTO, Pedido.ESTADO_ENTREGADO}:
            return Response({"detail": "El pedido ya no puede volver a preparacion."}, status=status.HTTP_400_BAD_REQUEST)
        if pedido.estado == Pedido.ESTADO_PREPARANDO:
            if pedido.preparado_por_id and pedido.preparado_por_id != request.user.id:
                return Response({"detail": "Este pedido ya lo esta preparando otro empleado."}, status=status.HTTP_403_FORBIDDEN)
            return Response(self.get_serializer(pedido).data)
        pedido.estado = Pedido.ESTADO_PREPARANDO
        pedido.preparado_por = request.user
        if not pedido.preparado_en:
            pedido.preparado_en = timezone.now()
        pedido.save(update_fields=["estado", "preparado_por", "preparado_en"])
        return Response(self.get_serializer(pedido).data)

    @action(detail=True, methods=["post"])
    def marcar_listo(self, request, pk=None):
        pedido = self.get_object()
        if pedido.estado == Pedido.ESTADO_ENTREGADO:
            return Response({"detail": "El pedido ya fue entregado."}, status=status.HTTP_400_BAD_REQUEST)
        if pedido.preparado_por_id and pedido.preparado_por_id != request.user.id:
            return Response({"detail": "Solo el empleado que inicio la preparacion puede marcarlo como listo."}, status=status.HTTP_403_FORBIDDEN)
        if not pedido.preparado_por:
            pedido.preparado_por = request.user
        if not pedido.preparado_en:
            pedido.preparado_en = timezone.now()
        pedido.estado = Pedido.ESTADO_LISTO
        pedido.listo_en = timezone.now()
        pedido.save(update_fields=["estado", "preparado_por", "preparado_en", "listo_en"])
        return Response(self.get_serializer(pedido).data)

    @action(detail=True, methods=["post"])
    def confirmar_salida(self, request, pk=None):
        pedido = self.get_object()
        pedido.confirmar_salida()
        return Response(self.get_serializer(pedido).data)


