from django.contrib.auth.models import User
from django.db.models import Avg
from rest_framework import serializers

from .models import ComentarioPlato, Ingrediente, Mesa, Pago, Pedido, PerfilUsuario, Plato, Receta, Reserva, ValoracionPlato, VotoComentario


class PerfilUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilUsuario
        fields = ["rol", "tema", "idioma", "nombre_mostrar", "telefono"]


class UsuarioSerializer(serializers.ModelSerializer):
    rol = serializers.ChoiceField(choices=PerfilUsuario.ROLE_CHOICES, write_only=True, required=False)
    tema = serializers.ChoiceField(choices=PerfilUsuario.THEME_CHOICES, write_only=True, required=False)
    idioma = serializers.ChoiceField(choices=PerfilUsuario.LANG_CHOICES, write_only=True, required=False)
    nombre_mostrar = serializers.CharField(write_only=True, required=False, allow_blank=True)
    telefono = serializers.CharField(write_only=True, required=False, allow_blank=True)
    perfil = PerfilUsuarioSerializer(read_only=True)
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "password", "rol", "tema", "idioma", "nombre_mostrar", "telefono", "perfil", "is_active"]

    def create(self, validated_data):
        rol = validated_data.pop("rol", PerfilUsuario.ROL_CLIENTE)
        tema = validated_data.pop("tema", PerfilUsuario.THEME_LIGHT)
        idioma = validated_data.pop("idioma", PerfilUsuario.LANG_ES)
        nombre_mostrar = validated_data.pop("nombre_mostrar", "")
        telefono = validated_data.pop("telefono", "")
        password = validated_data.pop("password")
        if nombre_mostrar and not validated_data.get("first_name"):
            validated_data["first_name"] = nombre_mostrar
        user = User.objects.create_user(password=password, **validated_data)
        PerfilUsuario.objects.create(user=user, rol=rol, tema=tema, idioma=idioma, nombre_mostrar=nombre_mostrar, telefono=telefono)
        user.is_staff = rol == PerfilUsuario.ROL_ADMIN
        user.save(update_fields=["is_staff"])
        return user


class PerfilUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilUsuario
        fields = ["tema", "idioma", "nombre_mostrar", "telefono"]


class MesaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mesa
        fields = "__all__"


class ReservaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reserva
        fields = "__all__"


class PagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pago
        fields = "__all__"


class IngredienteSerializer(serializers.ModelSerializer):
    alerta_roja = serializers.SerializerMethodField()

    class Meta:
        model = Ingrediente
        fields = "__all__"

    def get_alerta_roja(self, obj):
        umbral = obj.umbral_alerta if obj.umbral_alerta is not None else obj.stock_minimo
        return obj.stock_actual <= umbral


class RecetaSerializer(serializers.ModelSerializer):
    ingrediente_nombre = serializers.CharField(source="ingrediente.nombre", read_only=True)

    class Meta:
        model = Receta
        fields = ["id", "ingrediente", "ingrediente_nombre", "cantidad"]


class PlatoSerializer(serializers.ModelSerializer):
    receta = RecetaSerializer(source="recetas", many=True, read_only=True)
    puede_prepararse = serializers.SerializerMethodField()
    valoracion_media = serializers.SerializerMethodField()
    total_valoraciones = serializers.SerializerMethodField()

    class Meta:
        model = Plato
        fields = ["id", "nombre", "descripcion", "precio", "disponible", "es_vegano", "es_halal", "receta", "puede_prepararse", "valoracion_media", "total_valoraciones"]

    def get_puede_prepararse(self, obj):
        request = self.context.get("request")
        cantidad = 1
        if request:
            try:
                cantidad = int(request.query_params.get("cantidad", 1))
            except ValueError:
                cantidad = 1
        return obj.puede_prepararse(max(cantidad, 1))

    def get_valoracion_media(self, obj):
        media = obj.valoraciones.aggregate(media=Avg("puntuacion"))["media"]
        return round(float(media), 2) if media is not None else None

    def get_total_valoraciones(self, obj):
        return obj.valoraciones.count()


class PedidoSerializer(serializers.ModelSerializer):
    plato_nombre = serializers.SerializerMethodField()
    puede_prepararse = serializers.SerializerMethodField()
    mesa_nombre = serializers.CharField(source="reserva.mesa.nombre", read_only=True)
    reserva_fecha = serializers.DateField(source="reserva.fecha", read_only=True)
    reserva_hora = serializers.TimeField(source="reserva.hora", read_only=True)
    preparado_por_username = serializers.CharField(source="preparado_por.username", read_only=True)
    preparado_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = "__all__"
        read_only_fields = [
            "ingredientes_descontados",
            "plato_nombre",
            "plato_texto",
            "puede_prepararse",
            "mesa_nombre",
            "reserva_fecha",
            "reserva_hora",
            "preparado_por_username",
            "preparado_por_nombre",
        ]

    def get_plato_nombre(self, obj):
        if obj.plato:
            return obj.plato.nombre
        return obj.plato_texto

    def get_puede_prepararse(self, obj):
        if not obj.plato:
            return False
        return obj.plato.puede_prepararse(cantidad=obj.cantidad)

    def get_preparado_por_nombre(self, obj):
        if not obj.preparado_por:
            return ""
        return obj.preparado_por.first_name or obj.preparado_por.username

    def create(self, validated_data):
        plato = validated_data.get("plato")
        cantidad = validated_data.get("cantidad", 1)
        if plato and not plato.puede_prepararse(cantidad=cantidad):
            raise serializers.ValidationError("No hay stock suficiente para preparar este plato.")
        if validated_data.get("plato"):
            validated_data["plato_texto"] = validated_data["plato"].nombre
        if not validated_data.get("precio") and validated_data.get("plato"):
            validated_data["precio"] = validated_data["plato"].precio * validated_data["cantidad"]
        return super().create(validated_data)


class PedidoClienteInputSerializer(serializers.Serializer):
    plato_id = serializers.IntegerField()
    cantidad = serializers.IntegerField(min_value=1, default=1)


class ReservaClienteSerializer(serializers.Serializer):
    nombre_cliente = serializers.CharField(max_length=150)
    email_cliente = serializers.EmailField()
    mesa_id = serializers.IntegerField()
    fecha = serializers.DateField()
    hora = serializers.TimeField()
    pedido_anticipado = serializers.BooleanField(default=True)
    metodo_pago = serializers.ChoiceField(choices=Pago.METODO_CHOICES, default=Pago.METODO_LOCAL)
    referencia_pago = serializers.CharField(max_length=80, required=False, allow_blank=True)
    pedidos = PedidoClienteInputSerializer(many=True)


class ValoracionPlatoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValoracionPlato
        fields = ["id", "plato", "email_cliente", "puntuacion", "creado_en"]
        read_only_fields = ["id", "plato", "creado_en"]


class ComentarioPlatoSerializer(serializers.ModelSerializer):
    likes = serializers.SerializerMethodField()
    dislikes = serializers.SerializerMethodField()

    class Meta:
        model = ComentarioPlato
        fields = ["id", "plato", "nombre_cliente", "email_cliente", "comentario", "creado_en", "likes", "dislikes"]
        read_only_fields = ["id", "plato", "creado_en", "likes", "dislikes"]

    def get_likes(self, obj):
        return obj.votos.filter(tipo=VotoComentario.TIPO_LIKE).count()

    def get_dislikes(self, obj):
        return obj.votos.filter(tipo=VotoComentario.TIPO_DISLIKE).count()


class VotoComentarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = VotoComentario
        fields = ["id", "comentario", "email_cliente", "tipo", "creado_en"]
        read_only_fields = ["id", "comentario", "creado_en"]
