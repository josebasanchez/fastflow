from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


class PerfilUsuario(models.Model):
    ROL_ADMIN = "administrador"
    ROL_EMPLEADO = "empleado"
    ROL_CLIENTE = "cliente"

    ROLE_CHOICES = [
        (ROL_ADMIN, "Administrador"),
        (ROL_EMPLEADO, "Empleado"),
        (ROL_CLIENTE, "Cliente"),
    ]
    THEME_LIGHT = "light"
    THEME_DARK = "dark"
    THEME_CHOICES = [
        (THEME_LIGHT, "Light"),
        (THEME_DARK, "Dark"),
    ]
    LANG_ES = "es"
    LANG_EN = "en"
    LANG_CHOICES = [
        (LANG_ES, "Espanol"),
        (LANG_EN, "English"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil")
    rol = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROL_EMPLEADO)
    tema = models.CharField(max_length=10, choices=THEME_CHOICES, default=THEME_LIGHT)
    idioma = models.CharField(max_length=2, choices=LANG_CHOICES, default=LANG_ES)
    nombre_mostrar = models.CharField(max_length=120, blank=True, default="")
    telefono = models.CharField(max_length=30, blank=True, default="")

    class Meta:
        db_table = "perfiles_usuarios"


class Mesa(models.Model):
    ESTADO_LIBRE = "libre"
    ESTADO_RESERVADA = "reservada"
    ESTADOS = [
        (ESTADO_LIBRE, "Libre"),
        (ESTADO_RESERVADA, "Reservada"),
        ("mantenimiento", "Mantenimiento"),
    ]

    nombre = models.CharField(max_length=50)
    disposicion = models.CharField(max_length=50, default="interior")
    capacidad = models.PositiveIntegerField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default=ESTADO_LIBRE)

    class Meta:
        db_table = "mesas"


class Reserva(models.Model):
    ESTADO_PENDIENTE = "pendiente"
    ESTADO_CONFIRMADA = "confirmada"
    ESTADO_COMPLETADA = "completada"
    ESTADO_CANCELADA = "cancelada"

    ESTADOS = [
        (ESTADO_PENDIENTE, "Pendiente"),
        (ESTADO_CONFIRMADA, "Confirmada"),
        (ESTADO_COMPLETADA, "Completada"),
        (ESTADO_CANCELADA, "Cancelada"),
    ]

    mesa = models.ForeignKey(Mesa, on_delete=models.CASCADE, related_name="reservas")
    email_cliente = models.EmailField(default="")
    nombre_cliente = models.CharField(max_length=150)
    fecha = models.DateField()
    hora = models.TimeField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default=ESTADO_PENDIENTE)
    pedido_anticipado = models.BooleanField(default=False)
    creado_en = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "reservas"


class Ingrediente(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    stock_actual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unidad = models.CharField(max_length=20, default="ud")
    stock_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    umbral_alerta = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = "ingredientes"


class Plato(models.Model):
    nombre = models.CharField(max_length=150, unique=True)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    disponible = models.BooleanField(default=True)
    es_vegano = models.BooleanField(default=False)
    es_halal = models.BooleanField(default=False)

    class Meta:
        db_table = "platos"

    def puede_prepararse(self, cantidad=1):
        recetas = self.recetas.select_related("ingrediente").all()
        if not recetas:
            return False
        cantidad = Decimal(cantidad)
        for receta in recetas:
            requerido = receta.cantidad * cantidad
            if receta.ingrediente.stock_actual < requerido:
                return False
        return True


class Receta(models.Model):
    plato = models.ForeignKey(Plato, on_delete=models.CASCADE, related_name="recetas")
    ingrediente = models.ForeignKey(Ingrediente, on_delete=models.CASCADE, related_name="recetas")
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "recetas"
        unique_together = ("plato", "ingrediente")


class Pedido(models.Model):
    ESTADO_PENDIENTE = "pendiente"
    ESTADO_PREPARANDO = "preparando"
    ESTADO_LISTO = "listo"
    ESTADO_ENTREGADO = "entregado"

    ESTADOS = [
        (ESTADO_PENDIENTE, "Pendiente"),
        (ESTADO_PREPARANDO, "Preparando"),
        (ESTADO_LISTO, "Listo"),
        (ESTADO_ENTREGADO, "Entregado"),
    ]

    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name="pedidos")
    plato_texto = models.CharField(max_length=150, db_column="plato", default="")
    plato = models.ForeignKey(
        Plato,
        on_delete=models.PROTECT,
        related_name="pedidos",
        db_column="plato_id",
        null=True,
        blank=True,
    )
    cantidad = models.PositiveIntegerField(default=1)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS, default=ESTADO_PENDIENTE)
    creado_en = models.DateTimeField(default=timezone.now)
    fecha_limite = models.DateTimeField(default=timezone.now)
    ingredientes_descontados = models.BooleanField(default=False)
    preparado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedidos_preparados",
    )
    preparado_en = models.DateTimeField(null=True, blank=True)
    listo_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "pedidos"

    def save(self, *args, **kwargs):
        if self.plato:
            self.plato_texto = self.plato.nombre
        if not self.precio and self.plato:
            self.precio = self.plato.precio * Decimal(self.cantidad)
        super().save(*args, **kwargs)

    @transaction.atomic
    def confirmar_salida(self):
        if self.ingredientes_descontados:
            return

        if not self.plato_id:
            raise ValidationError("Pedido sin plato asociado a catalogo.")

        receta_items = list(self.plato.recetas.select_related("ingrediente").all())
        if not receta_items:
            raise ValidationError("El plato no tiene receta configurada.")

        for receta in receta_items:
            requerido = receta.cantidad * Decimal(self.cantidad)
            if receta.ingrediente.stock_actual < requerido:
                raise ValidationError(
                    f"Stock insuficiente de {receta.ingrediente.nombre}. Requerido: {requerido} {receta.ingrediente.unidad}"
                )

        for receta in receta_items:
            requerido = receta.cantidad * Decimal(self.cantidad)
            ingrediente = receta.ingrediente
            ingrediente.stock_actual -= requerido
            ingrediente.save(update_fields=["stock_actual"])

        self.estado = self.ESTADO_ENTREGADO
        self.ingredientes_descontados = True
        self.save(update_fields=["estado", "ingredientes_descontados"])


class Pago(models.Model):
    METODO_LOCAL = "establecimiento"
    METODO_BIZUM = "bizum"
    METODO_TARJETA = "tarjeta"
    METODO_CHOICES = [
        (METODO_LOCAL, "Pago en establecimiento"),
        (METODO_BIZUM, "Bizum"),
        (METODO_TARJETA, "Tarjeta"),
    ]
    ESTADO_PENDIENTE = "pendiente"
    ESTADO_APROBADO = "aprobado"
    ESTADO_RECHAZADO = "rechazado"
    ESTADO_CHOICES = [
        (ESTADO_PENDIENTE, "Pendiente"),
        (ESTADO_APROBADO, "Aprobado"),
        (ESTADO_RECHAZADO, "Rechazado"),
    ]

    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name="pagos")
    metodo = models.CharField(max_length=20, choices=METODO_CHOICES, default=METODO_LOCAL)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_PENDIENTE)
    referencia = models.CharField(max_length=80, blank=True, default="")
    importe = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    creado_en = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "pagos"


class ValoracionPlato(models.Model):
    plato = models.ForeignKey(Plato, on_delete=models.CASCADE, related_name="valoraciones")
    email_cliente = models.EmailField()
    puntuacion = models.PositiveSmallIntegerField()
    creado_en = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "valoraciones_plato"
        unique_together = ("plato", "email_cliente")


class ComentarioPlato(models.Model):
    plato = models.ForeignKey(Plato, on_delete=models.CASCADE, related_name="comentarios")
    nombre_cliente = models.CharField(max_length=150)
    email_cliente = models.EmailField()
    comentario = models.TextField(max_length=1000)
    creado_en = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "comentarios_plato"
        ordering = ["-creado_en"]


class VotoComentario(models.Model):
    TIPO_LIKE = "like"
    TIPO_DISLIKE = "dislike"
    TIPO_CHOICES = [
        (TIPO_LIKE, "Like"),
        (TIPO_DISLIKE, "Dislike"),
    ]

    comentario = models.ForeignKey(ComentarioPlato, on_delete=models.CASCADE, related_name="votos")
    email_cliente = models.EmailField()
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    creado_en = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "votos_comentario"
        unique_together = ("comentario", "email_cliente")
