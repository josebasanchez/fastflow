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

        # Empleados adicionales
        empleados_demo = [
            ("empleado2", "empleado1234", "empleado2@fastflow.es", "Empleado 2", "600000003"),
            ("empleado3", "empleado1234", "empleado3@fastflow.es", "Roberto Vega", "600000004"),
            ("empleado4", "empleado1234", "empleado4@fastflow.es", "Cristina Ramos", "600000005"),
            ("empleado5", "empleado1234", "empleado5@fastflow.es", "Alberto Prieto", "600000006"),
            ("empleado6", "empleado1234", "empleado6@fastflow.es", "Marta Silva", "600000007"),
            ("empleado7", "empleado1234", "empleado7@fastflow.es", "Fernando Castro", "600000008"),
        ]
        for username, password, email, nombre, telefono in empleados_demo:
            emp, created = User.objects.get_or_create(username=username)
            if created:
                emp.set_password(password)
            emp.is_staff = False
            emp.is_superuser = False
            emp.first_name = nombre
            emp.email = email
            emp.save()
            PerfilUsuario.objects.update_or_create(
                user=emp,
                defaults={
                    "rol": PerfilUsuario.ROL_EMPLEADO,
                    "tema": PerfilUsuario.THEME_LIGHT,
                    "idioma": PerfilUsuario.LANG_ES,
                    "nombre_mostrar": nombre,
                    "telefono": telefono,
                },
            )
        
        clientes_demo = [
            ("cliente1", "cliente1234", "cliente1@fastflow.es", "Cliente 1", "600000101"),
            ("cliente2", "cliente1234", "cliente2@fastflow.es", "Cliente 2", "600000102"),
            ("cliente3", "cliente1234", "cliente3@fastflow.es", "Ana García", "600000103"),
            ("cliente4", "cliente1234", "cliente4@fastflow.es", "Carlos Ruiz", "600000104"),
            ("cliente5", "cliente1234", "cliente5@fastflow.es", "María López", "600000105"),
            ("cliente6", "cliente1234", "cliente6@fastflow.es", "David Martín", "600000106"),
            ("cliente7", "cliente1234", "cliente7@fastflow.es", "Laura Sánchez", "600000107"),
            ("cliente8", "cliente1234", "cliente8@fastflow.es", "Jorge Fernández", "600000108"),
            ("cliente9", "cliente1234", "cliente9@fastflow.es", "Elena Díaz", "600000109"),
            ("cliente10", "cliente1234", "cliente10@fastflow.es", "Pablo Torres", "600000110"),
            ("cliente11", "cliente1234", "cliente11@fastflow.es", "Carmen Jiménez", "600000111"),
            ("cliente12", "cliente1234", "cliente12@fastflow.es", "Miguel Rodríguez", "600000112"),
            ("cliente13", "cliente1234", "cliente13@fastflow.es", "Isabel Moreno", "600000113"),
            ("cliente14", "cliente1234", "cliente14@fastflow.es", "Andrés Romero", "600000114"),
            ("cliente15", "cliente1234", "cliente15@fastflow.es", "Lucía Navarro", "600000115"),
            ("cliente16", "cliente1234", "cliente16@fastflow.es", "Javier Muñoz", "600000116"),
            ("cliente17", "cliente1234", "cliente17@fastflow.es", "Sofía Álvarez", "600000117"),
            ("cliente18", "cliente1234", "cliente18@fastflow.es", "Daniel Castillo", "600000118"),
            ("cliente19", "cliente1234", "cliente19@fastflow.es", "Patricia Ortiz", "600000119"),
            ("cliente20", "cliente1234", "cliente20@fastflow.es", "Raúl Delgado", "600000120"),
            ("cliente21", "cliente1234", "cliente21@fastflow.es", "Beatriz Herrera", "600000121"),
            ("cliente22", "cliente1234", "cliente22@fastflow.es", "Sergio Domínguez", "600000122"),
            ("cliente23", "cliente1234", "cliente23@fastflow.es", "Natalia Campos", "600000123"),
            ("cliente24", "cliente1234", "cliente24@fastflow.es", "Víctor Molina", "600000124"),
            ("cliente25", "cliente1234", "cliente25@fastflow.es", "Cristina Vargas", "600000125"),
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

        # Comentarios y valoraciones por plato - AMPLIADO
        sample_comments = [
            # Comentarios muy positivos
            "¡Excelente! Uno de los mejores platos que he probado aquí.",
            "Simplemente delicioso, volveré seguro.",
            "Superó mis expectativas, muy recomendable.",
            "La calidad es increíble, vale cada euro.",
            "Perfectamente preparado, no puedo poner ninguna pega.",
            "¡Espectacular! La presentación y el sabor son de 10.",
            "Me ha encantado, es mi plato favorito del menú.",
            "Riquísimo, las porciones son generosas.",
            "La mejor opción del restaurante sin duda.",
            
            # Comentarios positivos
            "Muy rico, repetiría.",
            "Buen sabor y buen punto de cocción.",
            "Calidad-precio correcta.",
            "Llegó rápido y caliente.",
            "La presentación está muy bien.",
            "Buena opción para comer algo rápido.",
            "Me gustó bastante, aunque esperaba algo más.",
            "Está bien, cumple con lo esperado.",
            "Sabor agradable y buenas cantidades.",
            "Recomendable si te gusta este tipo de comida.",
            "Correcto, sin ser extraordinario.",
            
            # Comentarios con sugerencias
            "Podría llevar un poco más de salsa.",
            "Estaría mejor con más condimentos.",
            "Le falta un toque de sabor, pero se come bien.",
            "Bueno, aunque la porción podría ser más grande.",
            "Rico, pero el precio es un poco elevado.",
            "Me gustó, pero he probado mejores versiones.",
            "Bien, aunque la temperatura podría mejorar.",
            "No está mal, pero le vendría bien más presentación.",
            
            # Comentarios neutros
            "Normal, nada del otro mundo.",
            "Está bien para salir del paso.",
            "Ni fu ni fa, esperaba más por el precio.",
            "Aceptable, pero no volvería a pedirlo.",
            "Es correcto, sin más.",
            
            # Comentarios negativos (algunos)
            "Demasiado salado para mi gusto.",
            "Esperaba más cantidad por ese precio.",
            "No me convenció, le falta sabor.",
            "La presentación no coincide con la foto del menú.",
            "Decepcionante, no repetiré.",
            
            # Comentarios sobre servicio
            "El plato llegó en tiempo récord, muy bien.",
            "Atención excelente y comida deliciosa.",
            "Tardó un poco pero mereció la pena.",
            "Servicio rápido y amable.",
            "La comida estaba fría cuando llegó.",
        ]
        
        # Ampliar lista de emails para votaciones
        vote_emails = [f"votante{i}@mail.com" for i in range(1, 50)]

        # Generar más comentarios por plato (entre 8 y 15 comentarios por plato)
        for plato in platos:
            num_comentarios = rng.randint(8, 15)
            for idx in range(num_comentarios):
                comentario = ComentarioPlato.objects.create(
                    plato=plato,
                    nombre_cliente=rng.choice([
                        "Ana García", "Carlos Ruiz", "María López", "David Martín",
                        "Laura Sánchez", "Jorge Fernández", "Elena Díaz", "Pablo Torres",
                        "Carmen Jiménez", "Miguel Rodríguez", "Isabel Moreno", "Andrés Romero",
                        "Lucía Navarro", "Javier Muñoz", "Sofía Álvarez", "Daniel Castillo",
                        "Patricia Ortiz", "Raúl Delgado", "Beatriz Herrera", "Sergio Domínguez",
                        "Cliente Satisfecho", "Foodie Salamanca", "Gourmet Local"
                    ]),
                    email_cliente=f"comentador{idx + 1}_{plato.id}@mail.com",
                    comentario=rng.choice(sample_comments),
                )

                # Generar votos aleatorios para cada comentario
                num_voters = rng.randint(3, 12)
                voters = rng.sample(vote_emails, k=num_voters)
                for email in voters:
                    # Mayoría de likes (70%), pero también algunos dislikes
                    tipo_voto = rng.choices(
                        [VotoComentario.TIPO_LIKE, VotoComentario.TIPO_DISLIKE],
                        weights=[0.7, 0.3]
                    )[0]
                    VotoComentario.objects.create(
                        comentario=comentario,
                        email_cliente=email,
                        tipo=tipo_voto,
                    )

            # Generar valoraciones (entre 6 y 12 por plato)
            num_valoraciones = rng.randint(6, 12)
            for idx in range(num_valoraciones):
                # Distribución más realista de puntuaciones
                puntuacion = rng.choices(
                    [1, 2, 3, 4, 5],
                    weights=[0.05, 0.10, 0.20, 0.35, 0.30]  # Mayoría entre 4 y 5
                )[0]
                ValoracionPlato.objects.update_or_create(
                    plato=plato,
                    email_cliente=f"rating{idx + 1}_{plato.id}@mail.com",
                    defaults={"puntuacion": puntuacion},
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
            platos.append(plato)  # Agregar a la lista para que también reciba comentarios
            for ing_nombre, cantidad in plato_data["receta"].items():
                Receta.objects.update_or_create(
                    plato=plato,
                    ingrediente=ing_map[ing_nombre],
                    defaults={"cantidad": cantidad},
                )
            
            # Generar comentarios también para los nuevos platos
            num_comentarios = rng.randint(8, 15)
            for idx in range(num_comentarios):
                comentario = ComentarioPlato.objects.create(
                    plato=plato,
                    nombre_cliente=rng.choice([
                        "Ana García", "Carlos Ruiz", "María López", "David Martín",
                        "Laura Sánchez", "Jorge Fernández", "Elena Díaz", "Pablo Torres",
                        "Cliente Satisfecho", "Foodie Salamanca"
                    ]),
                    email_cliente=f"nuevo_comentador{idx + 1}_{plato.id}@mail.com",
                    comentario=rng.choice(sample_comments),
                )

                num_voters = rng.randint(3, 12)
                voters = rng.sample(vote_emails, k=num_voters)
                for email in voters:
                    tipo_voto = rng.choices(
                        [VotoComentario.TIPO_LIKE, VotoComentario.TIPO_DISLIKE],
                        weights=[0.7, 0.3]
                    )[0]
                    VotoComentario.objects.create(
                        comentario=comentario,
                        email_cliente=email,
                        tipo=tipo_voto,
                    )

            num_valoraciones = rng.randint(6, 12)
            for idx in range(num_valoraciones):
                puntuacion = rng.choices(
                    [1, 2, 3, 4, 5],
                    weights=[0.05, 0.10, 0.20, 0.35, 0.30]
                )[0]
                ValoracionPlato.objects.update_or_create(
                    plato=plato,
                    email_cliente=f"nuevo_rating{idx + 1}_{plato.id}@mail.com",
                    defaults={"puntuacion": puntuacion},
                )

        self.stdout.write(self.style.SUCCESS("Datos ficticios cargados correctamente."))
        self.stdout.write("=" * 60)
        self.stdout.write("USUARIOS CREADOS:")
        self.stdout.write("-" * 60)
        self.stdout.write("Admin: admin / admin1234")
        self.stdout.write("")
        self.stdout.write("Empleados (todos con password: empleado1234):")
        self.stdout.write("  - empleado1, empleado2, empleado3, empleado4, empleado5, empleado6, empleado7")
        self.stdout.write("")
        self.stdout.write("Clientes (todos con password: cliente1234):")
        self.stdout.write("  - cliente1 a cliente25 (25 clientes en total)")
        self.stdout.write("")
        self.stdout.write(f"Total de comentarios generados: ~{len(platos) * 11} comentarios")
        self.stdout.write(f"Total de valoraciones generadas: ~{len(platos) * 9} valoraciones")
        self.stdout.write("=" * 60)
        self.stdout.write("No se han generado reservas automaticamente.")
