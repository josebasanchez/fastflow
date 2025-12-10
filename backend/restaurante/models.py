from django.db import models


class Mesa(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)
    capacidad = models.IntegerField()
    estado = models.CharField(
        max_length=20,
        choices=[
            ('libre', 'Libre'),
            ('reservada', 'Reservada'),
            ('mantenimiento', 'Mantenimiento'),
        ],
        default='libre'
    )

    class Meta:
        managed = False
        db_table = 'mesas'


class Reserva(models.Model):
    id = models.AutoField(primary_key=True)
    mesa = models.ForeignKey(
        Mesa,
        on_delete=models.CASCADE,
        db_column='mesa_id'
    )
    nombre_cliente = models.CharField(max_length=150)
    fecha = models.DateField()
    hora = models.TimeField()
    estado = models.CharField(
        max_length=20,
        choices=[
            ('pendiente', 'Pendiente'),
            ('confirmada', 'Confirmada'),
            ('completada', 'Completada'),
            ('cancelada', 'Cancelada'),
        ],
        default='pendiente'
    )
    pedido_anticipado = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=False)

    class Meta:
        managed = False
        db_table = 'reservas'


class Pedido(models.Model):
    id = models.AutoField(primary_key=True)
    reserva = models.ForeignKey(
        Reserva,
        on_delete=models.CASCADE,
        db_column='reserva_id'
    )
    plato = models.CharField(max_length=150)
    cantidad = models.IntegerField(default=1)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(
        max_length=20,
        choices=[
            ('pendiente', 'Pendiente'),
            ('preparando', 'Preparando'),
            ('listo', 'Listo'),
            ('entregado', 'Entregado'),
        ],
        default='pendiente'
    )
    creado_en = models.DateTimeField(auto_now_add=False)

    class Meta:
        managed = False
        db_table = 'pedidos'


class Usuario(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    email = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=255)
    rol = models.CharField(
        max_length=20,
        choices=[
            ('admin', 'Admin'),
            ('empleado', 'Empleado'),
            ('cliente', 'Cliente'),
        ],
        default='cliente'
    )
    creado_en = models.DateTimeField(auto_now_add=False)

    class Meta:
        managed = False
        db_table = 'usuarios'
