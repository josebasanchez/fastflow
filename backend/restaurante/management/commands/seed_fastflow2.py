from decimal import Decimal
from datetime import date, datetime, time

from django.core.management.base import BaseCommand
from django.utils import timezone

from restaurante.models import Ingrediente, Mesa, Pedido, Plato, Receta, Reserva


class Command(BaseCommand):
    help = "Carga catalogo adicional de FastFlow sin reiniciar datos"

    def handle(self, *args, **options):
        ingredientes_extra = [
            ("Refresco cola", Decimal("220"), "l", Decimal("30")),
            ("Agua mineral", Decimal("260"), "l", Decimal("30")),
            ("Cafe molido", Decimal("20"), "kg", Decimal("4")),
            ("Zumo naranja", Decimal("180"), "l", Decimal("25")),
            ("Alitas pollo", Decimal("40"), "kg", Decimal("8")),
            ("Nuggets pollo", Decimal("30"), "kg", Decimal("6")),
            ("Chocolate", Decimal("25"), "kg", Decimal("5")),
        ]

        ing_map = {}
        for nombre, stock, unidad, minimo in ingredientes_extra:
            ingrediente, _ = Ingrediente.objects.update_or_create(
                nombre=nombre,
                defaults={
                    "stock_actual": stock,
                    "unidad": unidad,
                    "stock_minimo": minimo,
                    "umbral_alerta": minimo,
                },
            )
            ing_map[nombre] = ingrediente

        # Ingredientes que deben existir por seed_fastflow original.
        base_required = [
            "Pan burger",
            "Carne vacuno",
            "Queso cheddar",
            "Lechuga",
            "Tomate",
            "Patatas",
            "Masa pizza",
            "Salsa tomate",
            "Mozzarella",
            "Pechuga pollo",
        ]
        for nombre in base_required:
            ingrediente = Ingrediente.objects.filter(nombre=nombre).first()
            if not ingrediente:
                self.stdout.write(
                    self.style.WARNING(
                        f"No existe ingrediente base '{nombre}'. Ejecuta primero seed_fastflow."
                    )
                )
                return
            ing_map[nombre] = ingrediente

        platos_extra = [
            {
                "nombre": "Pizza Cuatro Quesos",
                "descripcion": "Pizza cremosa con mezcla de quesos fundidos",
                "precio": Decimal("12.50"),
                "es_vegano": False,
                "es_halal": True,
                "receta": {
                    "Masa pizza": Decimal("1"),
                    "Salsa tomate": Decimal("0.10"),
                    "Mozzarella": Decimal("0.20"),
                    "Queso cheddar": Decimal("0.05"),
                },
            },
            {
                "nombre": "Ensalada Mediterranea",
                "descripcion": "Ensalada fresca de tomate, lechuga y queso",
                "precio": Decimal("8.90"),
                "es_vegano": False,
                "es_halal": True,
                "receta": {
                    "Lechuga": Decimal("0.20"),
                    "Tomate": Decimal("0.20"),
                    "Mozzarella": Decimal("0.08"),
                },
            },
            {
                "nombre": "Burger Doble BBQ",
                "descripcion": "Doble burger de vacuno con cheddar y tomate",
                "precio": Decimal("14.20"),
                "es_vegano": False,
                "es_halal": False,
                "receta": {
                    "Pan burger": Decimal("1"),
                    "Carne vacuno": Decimal("0.25"),
                    "Queso cheddar": Decimal("0.05"),
                    "Lechuga": Decimal("0.05"),
                    "Tomate": Decimal("0.10"),
                    "Patatas": Decimal("0.20"),
                },
            },
            {
                "nombre": "Hamburguesa BBQ Bacon",
                "descripcion": "Hamburguesa de vacuno con salsa BBQ y cheddar",
                "precio": Decimal("13.50"),
                "es_vegano": False,
                "es_halal": False,
                "receta": {
                    "Pan burger": Decimal("1"),
                    "Carne vacuno": Decimal("0.20"),
                    "Queso cheddar": Decimal("0.04"),
                    "Lechuga": Decimal("0.05"),
                    "Tomate": Decimal("0.10"),
                    "Patatas": Decimal("0.20"),
                },
            },
            {
                "nombre": "Hamburguesa Crispy Pollo",
                "descripcion": "Hamburguesa de pollo crujiente con lechuga y tomate",
                "precio": Decimal("12.80"),
                "es_vegano": False,
                "es_halal": True,
                "receta": {
                    "Pan burger": Decimal("1"),
                    "Pechuga pollo": Decimal("0.18"),
                    "Lechuga": Decimal("0.06"),
                    "Tomate": Decimal("0.10"),
                    "Patatas": Decimal("0.20"),
                },
            },
            {
                "nombre": "Menu Burger + Cola",
                "descripcion": "Menu completo con hamburguesa clasica, patatas y cola",
                "precio": Decimal("15.50"),
                "es_vegano": False,
                "es_halal": False,
                "receta": {
                    "Pan burger": Decimal("1"),
                    "Carne vacuno": Decimal("0.18"),
                    "Queso cheddar": Decimal("0.03"),
                    "Lechuga": Decimal("0.05"),
                    "Tomate": Decimal("0.10"),
                    "Patatas": Decimal("0.25"),
                    "Refresco cola": Decimal("0.33"),
                },
            },
            {
                "nombre": "Menu Pizza + Agua",
                "descripcion": "Menu pizza margarita con agua y patatas",
                "precio": Decimal("14.90"),
                "es_vegano": False,
                "es_halal": True,
                "receta": {
                    "Masa pizza": Decimal("1"),
                    "Salsa tomate": Decimal("0.12"),
                    "Mozzarella": Decimal("0.15"),
                    "Patatas": Decimal("0.20"),
                    "Agua mineral": Decimal("0.50"),
                },
            },
            {
                "nombre": "Patatas Fries",
                "descripcion": "Patatas fries crujientes con sal",
                "precio": Decimal("4.50"),
                "es_vegano": True,
                "es_halal": True,
                "receta": {
                    "Patatas": Decimal("0.25"),
                },
            },
            {
                "nombre": "Alitas BBQ",
                "descripcion": "Alitas de pollo al horno con salsa barbacoa",
                "precio": Decimal("7.90"),
                "es_vegano": False,
                "es_halal": False,
                "receta": {
                    "Alitas pollo": Decimal("0.30"),
                    "Salsa tomate": Decimal("0.05"),
                },
            },
            {
                "nombre": "Nuggets de Pollo",
                "descripcion": "Nuggets crujientes de pollo",
                "precio": Decimal("6.90"),
                "es_vegano": False,
                "es_halal": True,
                "receta": {
                    "Nuggets pollo": Decimal("0.25"),
                },
            },
            {
                "nombre": "Cola Lata",
                "descripcion": "Refresco cola frio",
                "precio": Decimal("2.50"),
                "es_vegano": True,
                "es_halal": True,
                "receta": {
                    "Refresco cola": Decimal("0.33"),
                },
            },
            {
                "nombre": "Agua Mineral",
                "descripcion": "Botella de agua mineral",
                "precio": Decimal("2.00"),
                "es_vegano": True,
                "es_halal": True,
                "receta": {
                    "Agua mineral": Decimal("0.50"),
                },
            },
            {
                "nombre": "Cafe Espresso",
                "descripcion": "Cafe espresso intenso",
                "precio": Decimal("1.90"),
                "es_vegano": True,
                "es_halal": True,
                "receta": {
                    "Cafe molido": Decimal("0.01"),
                    "Agua mineral": Decimal("0.03"),
                },
            },
            {
                "nombre": "Zumo de Naranja",
                "descripcion": "Zumo natural de naranja",
                "precio": Decimal("2.80"),
                "es_vegano": True,
                "es_halal": True,
                "receta": {
                    "Zumo naranja": Decimal("0.30"),
                },
            },
            {
                "nombre": "Brownie Chocolate",
                "descripcion": "Postre casero de chocolate",
                "precio": Decimal("4.20"),
                "es_vegano": False,
                "es_halal": True,
                "receta": {
                    "Chocolate": Decimal("0.08"),
                },
            },
        ]

        for plato_data in platos_extra:
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

        reserva_seeds = [
            {
                "mesa": "M1",
                "fecha": date(2026, 5, 27),
                "hora": time(13, 30),
                "nombre_cliente": "Reserva Seed 1",
                "email_cliente": "seed2.reserva1@fastflow.es",
                "pedidos": [("Hamburguesa Clasica", 1), ("Patatas Fries", 1), ("Cola Lata", 1)],
            },
            {
                "mesa": "M2",
                "fecha": date(2026, 5, 28),
                "hora": time(14, 0),
                "nombre_cliente": "Reserva Seed 2",
                "email_cliente": "seed2.reserva2@fastflow.es",
                "pedidos": [("Pizza Margarita", 1), ("Agua Mineral", 2), ("Brownie Chocolate", 1)],
            },
            {
                "mesa": "M3",
                "fecha": date(2026, 5, 29),
                "hora": time(21, 0),
                "nombre_cliente": "Reserva Seed 3",
                "email_cliente": "seed2.reserva3@fastflow.es",
                "pedidos": [("Menu Burger + Cola", 2), ("Nuggets de Pollo", 1)],
            },
            {
                "mesa": "M4",
                "fecha": date(2026, 5, 30),
                "hora": time(20, 30),
                "nombre_cliente": "Reserva Seed 4",
                "email_cliente": "seed2.reserva4@fastflow.es",
                "pedidos": [("Menu Pizza + Agua", 1), ("Ensalada Mediterranea", 1), ("Zumo de Naranja", 1)],
            },
        ]

        reservas_creadas = 0
        pedidos_procesados = 0
        mesas_actualizadas = 0

        for item in reserva_seeds:
            mesa = Mesa.objects.filter(nombre=item["mesa"]).first()
            if not mesa:
                self.stdout.write(
                    self.style.WARNING(
                        f"No existe la mesa '{item['mesa']}'. Ejecuta seed_fastflow para crear mesas base."
                    )
                )
                continue

            reserva, creada = Reserva.objects.update_or_create(
                mesa=mesa,
                fecha=item["fecha"],
                hora=item["hora"],
                email_cliente=item["email_cliente"],
                defaults={
                    "nombre_cliente": item["nombre_cliente"],
                    "estado": Reserva.ESTADO_CONFIRMADA,
                    "pedido_anticipado": True,
                },
            )
            if creada:
                reservas_creadas += 1

            if mesa.estado != Mesa.ESTADO_RESERVADA:
                mesa.estado = Mesa.ESTADO_RESERVADA
                mesa.save(update_fields=["estado"])
                mesas_actualizadas += 1

            for plato_nombre, cantidad in item["pedidos"]:
                plato = Plato.objects.filter(nombre=plato_nombre).first()
                if not plato:
                    self.stdout.write(
                        self.style.WARNING(
                            f"No existe plato '{plato_nombre}'. Se omite pedido para reserva {reserva.id}."
                        )
                    )
                    continue

                fecha_limite = timezone.make_aware(
                    datetime.combine(item["fecha"], item["hora"])
                )

                Pedido.objects.update_or_create(
                    reserva=reserva,
                    plato=plato,
                    defaults={
                        "plato_texto": plato.nombre,
                        "cantidad": cantidad,
                        "precio": plato.precio * Decimal(cantidad),
                        "estado": Pedido.ESTADO_PENDIENTE,
                        "fecha_limite": fecha_limite,
                        "ingredientes_descontados": False,
                    },
                )
                pedidos_procesados += 1

        self.stdout.write(self.style.SUCCESS("seed_fastflow2 aplicado sin reiniciar datos."))
        self.stdout.write(f"Ingredientes extra procesados: {len(ingredientes_extra)}")
        self.stdout.write(f"Platos extra procesados: {len(platos_extra)}")
        self.stdout.write(
            "Reservas sembradas para 27, 28, 29 y 30 de mayo de 2026: "
            f"{len(reserva_seeds)} (nuevas: {reservas_creadas})"
        )
        self.stdout.write(f"Pedidos procesados en reservas: {pedidos_procesados}")
        self.stdout.write(f"Mesas marcadas como reservadas: {mesas_actualizadas}")
