from decimal import Decimal
import random

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from restaurante.models import (
    ComentarioPlato,
    Ingrediente,
    Mesa,
    PerfilUsuario,
    Plato,
    Receta,
    ValoracionPlato,
    VotoComentario,
)


class Command(BaseCommand):
    help = "Carga datos ficticios base para FastFlow"
    
    # def _reset_seed_data(self):
    #     """
    #     Limpia datos previamente sembrados sin romper si faltan tablas.
    #     """
    #     print("Limpiando datos sembrados anteriormente...")

    #     safe_delete(VotoComentario, "restaurante_votocomentario")
    #     safe_delete(ComentarioPlato, "restaurante_comentarioplato")
    #     safe_delete(ValoracionPlato, "restaurante_valoracionplato")
    #     safe_delete(Pago, "restaurante_pago")
    #     safe_delete(Pedido, "restaurante_pedido")
    #     safe_delete(Reserva, "restaurante_reserva")

    # def table_exists(table_name: str) -> bool:
    #     return table_name in connection.introspection.table_names()


    # def safe_delete(model, table_name: str):
    #     try:
    #         if table_exists(table_name):
    #             model.objects.all().delete()
    #         else:
    #             print(f"⚠️ Tabla {table_name} no existe, se omite")
    #     except Exception as e:
    #         print(f"⚠️ Error borrando {table_name}: {e}")
    def handle(self, *args, **options):
        # Limpia datos previos antes de sembrar para evitar crecimiento infinito.
        call_command("flush", interactive=False)

        rng = random.Random(20260503)

        # Paso 1: eliminar lo sembrado anteriormente (datos transaccionales).
        # self.stdout.write("Limpiando datos sembrados anteriormente...")
        # self._reset_seed_data()

        admin, created = User.objects.get_or_create(username="admin")
        if created:
            admin.set_password("admin1234")
        admin.is_staff = True
        admin.is_superuser = True
        admin.first_name = "Administrador"
        admin.email = "admin@fastflow.es"
        admin.save()
        PerfilUsuario.objects.update_or_create(
            user=admin,
            defaults={
                "rol": PerfilUsuario.ROL_ADMIN,
                "tema": PerfilUsuario.THEME_LIGHT,
                "idioma": PerfilUsuario.LANG_ES,
                "nombre_mostrar": "Administrador",
                "telefono": "600000001",
            },
        )

        empleado, created = User.objects.get_or_create(username="empleado1")
        if created:
            empleado.set_password("empleado1234")
        empleado.is_staff = False
        empleado.is_superuser = False
        empleado.first_name = "Empleado 1"
        empleado.email = "empleado1@fastflow.es"
        empleado.save()
        PerfilUsuario.objects.update_or_create(
            user=empleado,
            defaults={
                "rol": PerfilUsuario.ROL_EMPLEADO,
                "tema": PerfilUsuario.THEME_LIGHT,
                "idioma": PerfilUsuario.LANG_ES,
                "nombre_mostrar": "Empleado 1",
                "telefono": "600000002",
            },
        )

        empleado2, created = User.objects.get_or_create(username="empleado2")
        if created:
            empleado2.set_password("empleado1234")
        empleado2.is_staff = False
        empleado2.is_superuser = False
        empleado2.first_name = "Empleado 2"
        empleado2.email = "empleado2@fastflow.es"
        empleado2.save()
        PerfilUsuario.objects.update_or_create(
            user=empleado2,
            defaults={
                "rol": PerfilUsuario.ROL_EMPLEADO,
                "tema": PerfilUsuario.THEME_LIGHT,
                "idioma": PerfilUsuario.LANG_ES,
                "nombre_mostrar": "Empleado 2",
                "telefono": "600000003",
            },
        )
        
        clientes_demo = [
            ("cliente1", "cliente1234", "cliente1@fastflow.es", "Cliente 1", "600000101"),
            ("cliente2", "cliente1234", "cliente2@fastflow.es", "Cliente 2", "600000102"),
        ]
        for username, password, email, nombre, telefono in clientes_demo:
            cliente, created = User.objects.get_or_create(username=username)
            if created:
                cliente.set_password(password)
            cliente.is_staff = False
            cliente.is_superuser = False
            cliente.first_name = nombre
            cliente.email = email
            cliente.save()
            PerfilUsuario.objects.update_or_create(
                user=cliente,
                defaults={
                    "rol": PerfilUsuario.ROL_CLIENTE,
                    "tema": PerfilUsuario.THEME_LIGHT,
                    "idioma": PerfilUsuario.LANG_ES,
                    "nombre_mostrar": nombre,
                    "telefono": telefono,
                },
            )

        mesas = [
            ("M1", 2), ("M2", 2), ("M3", 3), ("M4", 5), ("M5", 5), ("M6", 8),
        ]
        mesa_objs = []
        for nombre, capacidad in mesas:
            mesa, _ = Mesa.objects.update_or_create(
                nombre=nombre,
                defaults={"capacidad": capacidad, "estado": Mesa.ESTADO_LIBRE},
            )
            mesa_objs.append(mesa)

        ingredientes = [
            ("Pan burger", Decimal("120"), "ud", Decimal("20")),
            ("Carne vacuno", Decimal("45"), "kg", Decimal("8")),
            ("Queso cheddar", Decimal("20"), "kg", Decimal("4")),
            ("Lechuga", Decimal("35"), "ud", Decimal("8")),
            ("Tomate", Decimal("50"), "ud", Decimal("10")),
            ("Patatas", Decimal("80"), "kg", Decimal("15")),
            ("Masa pizza", Decimal("40"), "ud", Decimal("8")),
            ("Salsa tomate", Decimal("30"), "kg", Decimal("6")),
            ("Mozzarella", Decimal("25"), "kg", Decimal("5")),
            ("Pechuga pollo", Decimal("30"), "kg", Decimal("6")),
        ]
        ing_map = {}
        for nombre, stock, unidad, minimo in ingredientes:
            ing, _ = Ingrediente.objects.update_or_create(
                nombre=nombre,
                defaults={"stock_actual": stock, "unidad": unidad, "stock_minimo": minimo, "umbral_alerta": minimo},
            )
            ing_map[nombre] = ing

        platos_data = [
            {
                "nombre": "Hamburguesa Clasica",
                "descripcion": "Carne de vacuno, cheddar, lechuga y tomate",
                "precio": Decimal("11.90"),
                "es_vegano": False,
                "es_halal": False,
                "receta": {
                    "Pan burger": Decimal("1"),
                    "Carne vacuno": Decimal("0.18"),
                    "Queso cheddar": Decimal("0.03"),
                    "Lechuga": Decimal("0.05"),
                    "Tomate": Decimal("0.10"),
                    "Patatas": Decimal("0.20"),
                },
            },
            {
                "nombre": "Pizza Margarita",
                "descripcion": "Masa artesanal con tomate y mozzarella",
                "precio": Decimal("10.50"),
                "es_vegano": False,
                "es_halal": True,
                "receta": {
                    "Masa pizza": Decimal("1"),
                    "Salsa tomate": Decimal("0.12"),
                    "Mozzarella": Decimal("0.15"),
                },
            },
            {
                "nombre": "Ensalada Cesar",
                "descripcion": "Pechuga de pollo con vegetales frescos",
                "precio": Decimal("9.50"),
                "es_vegano": False,
                "es_halal": False,
                "receta": {
                    "Pechuga pollo": Decimal("0.12"),
                    "Lechuga": Decimal("0.20"),
                    "Tomate": Decimal("0.15"),
                    "Queso cheddar": Decimal("0.02"),
                },
            },
            {
                "nombre": "Burger Vegana",
                "descripcion": "Pan, lechuga y tomate con base vegetal",
                "precio": Decimal("12.20"),
                "es_vegano": True,
                "es_halal": True,
                "receta": {
                    "Pan burger": Decimal("1"),
                    "Lechuga": Decimal("0.08"),
                    "Tomate": Decimal("0.12"),
                    "Patatas": Decimal("0.20"),
                },
            },
        ]

        platos = []
        for plato_data in platos_data:
            plato, _ = Plato.objects.update_or_create(
                nombre=plato_data["nombre"],
                defaults={
                    "descripcion": plato_data["descripcion"],
                    "precio": plato_data["precio"],
                    "disponible": True,
                    "es_vegano": plato_data["es_vegano"],
                    "es_halal": plato_data["es_halal"],
                },
            )
            platos.append(plato)
            for ing_nombre, cantidad in plato_data["receta"].items():
                Receta.objects.update_or_create(
                    plato=plato,
                    ingrediente=ing_map[ing_nombre],
                    defaults={"cantidad": cantidad},
                )

        # Comentarios y valoraciones por plato.
        sample_comments = [
            "Muy rico, repetiría.",
            "Buen sabor y buen punto de cocción.",
            "Calidad-precio correcta.",
            "Llegó rápido y caliente.",
            "Podría llevar un poco más de salsa.",
            "La presentación está muy bien.",
        ]
        vote_emails = [f"cliente{i}@mail.com" for i in range(1, 19)]

        for plato in platos:
            for idx in range(4):
                comentario = ComentarioPlato.objects.create(
                    plato=plato,
                    nombre_cliente=f"Cliente {idx + 1}",
                    email_cliente=f"comentador{idx + 1}@mail.com",
                    comentario=rng.choice(sample_comments),
                )

                voters = rng.sample(vote_emails, k=rng.randint(4, 10))
                for email in voters:
                    VotoComentario.objects.create(
                        comentario=comentario,
                        email_cliente=email,
                        tipo=rng.choice([VotoComentario.TIPO_LIKE, VotoComentario.TIPO_DISLIKE]),
                    )

                ValoracionPlato.objects.update_or_create(
                    plato=plato,
                    email_cliente=f"rating{idx + 1}@mail.com",
                    defaults={"puntuacion": rng.randint(3, 5)},
                )
        # No se crean reservas ni pedidos historicos desde el seed para que puedas gestionarlos manualmente.

        # Agregar nuevos platos con ingredientes diversos
        nuevos_platos = [
            {
                "nombre": "Tacos al Pastor",
                "descripcion": "Tacos de cerdo marinados con piña y especias",
                "precio": Decimal("8.50"),
                "es_vegano": False,
                "es_halal": False,
                "receta": {
                    "Carne vacuno": Decimal("0.15"),
                    "Tomate": Decimal("0.10"),
                    "Lechuga": Decimal("0.05"),
                },
            },
            {
                "nombre": "Sopa de Miso",
                "descripcion": "Sopa japonesa con tofu y algas",
                "precio": Decimal("6.00"),
                "es_vegano": True,
                "es_halal": True,
                "receta": {
                    "Salsa tomate": Decimal("0.05"),
                    "Mozzarella": Decimal("0.02"),
                },
            },
        ]

        for plato_data in nuevos_platos:
            plato, _ = Plato.objects.update_or_create(
                nombre=plato_data["nombre"],
                defaults={
                    "descripcion": plato_data["descripcion"],
                    "precio": plato_data["precio"],
                    "disponible": True,
                    "es_vegano": plato_data["es_vegano"],
                    "es_halal": plato_data["es_halal"],
                },
            )
            for ing_nombre, cantidad in plato_data["receta"].items():
                Receta.objects.update_or_create(
                    plato=plato,
                    ingrediente=ing_map[ing_nombre],
                    defaults={"cantidad": cantidad},
                )

        self.stdout.write(self.style.SUCCESS("Datos ficticios cargados correctamente."))
        self.stdout.write("Admin: admin / admin1234")
        self.stdout.write("Empleado: empleado1 / empleado1234")
        self.stdout.write("Empleado: empleado2 / empleado1234")
        self.stdout.write("Cliente: cliente1 / cliente1234")
        self.stdout.write("Cliente: cliente2 / cliente1234")
        self.stdout.write("No se han generado reservas automaticamente.")


