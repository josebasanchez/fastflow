from __future__ import annotations

import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from restaurante.models import Mesa, Pago, Pedido, Plato, Reserva


class Command(BaseCommand):
    help = (
        "Seed demo para la presentacion (28/05/2026 10:30): "
        "cola de pedidos con urgencias/colores y historico realista 14 dias para admin."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--anchor",
            default="2026-05-28T10:30",
            help="Fecha/hora local (ISO) para anclar la demo. Ej: 2026-05-28T10:30",
        )

    def handle(self, *args, **options):
        rng = random.Random(20260528)
        tz = timezone.get_current_timezone()

        anchor_raw = str(options.get("anchor") or "").strip()
        try:
            anchor_naive = datetime.fromisoformat(anchor_raw)
        except ValueError:
            raise SystemExit(
                f"Formato invalido para --anchor: '{anchor_raw}'. Usa ISO, por ejemplo 2026-05-28T10:30."
            )
        anchor = timezone.make_aware(anchor_naive, tz) if timezone.is_naive(anchor_naive) else anchor_naive.astimezone(tz)
        anchor_date = anchor.date()
        inicio_14d = anchor_date - timedelta(days=13)

        # Modo append-only: no borra nada. Para evitar duplicados al re-ejecutar,
        # el seed usa claves deterministas con update_or_create donde aplica.

        empleados = list(
            User.objects.filter(username__startswith="empleado").order_by("username")
        )
        if not empleados:
            self.stdout.write(
                self.style.WARNING(
                    "No existen usuarios empleado*. Ejecuta primero seed_fastflow."
                )
            )
            return

        mesas = list(Mesa.objects.all().order_by("nombre"))
        if not mesas:
            self.stdout.write(
                self.style.WARNING("No existen mesas. Ejecuta primero seed_fastflow.")
            )
            return

        platos = list(Plato.objects.filter(disponible=True).order_by("id"))
        if not platos:
            self.stdout.write(
                self.style.WARNING("No existen platos. Ejecuta primero seed_fastflow.")
            )
            return

        def aware(dt: datetime) -> datetime:
            if timezone.is_aware(dt):
                return dt
            return timezone.make_aware(dt, tz)

        def pick_cliente(i: int) -> tuple[str, str]:
            nombres = [
                "Ana Garcia",
                "Carlos Ruiz",
                "Maria Lopez",
                "David Martin",
                "Laura Sanchez",
                "Jorge Fernandez",
                "Elena Diaz",
                "Pablo Torres",
                "Carmen Jimenez",
                "Miguel Rodriguez",
                "Isabel Moreno",
                "Andres Romero",
                "Lucia Navarro",
                "Javier Munoz",
                "Sofia Alvarez",
                "Daniel Castillo",
                "Patricia Ortiz",
                "Raul Delgado",
                "Beatriz Herrera",
                "Sergio Dominguez",
                "Natalia Campos",
                "Victor Molina",
                "Cristina Vargas",
                "Empresa ACME (evento)",
                "Cumpleanos Paula (familia)",
            ]
            nombre = nombres[i % len(nombres)]
            email = f"demo{anchor_date.strftime('%Y%m%d')}.{i}@fastflow.es"
            return nombre, email

        def get_or_create_reserva(
            *,
            mesa: Mesa,
            fecha: date,
            hora: time,
            nombre_cliente: str,
            email_cliente: str,
            estado: str,
            pedido_anticipado: bool,
            creado_en: datetime,
        ) -> Reserva:
            reserva, _ = Reserva.objects.update_or_create(
                mesa=mesa,
                fecha=fecha,
                hora=hora,
                email_cliente=email_cliente,
                defaults={
                    "nombre_cliente": nombre_cliente,
                    "estado": estado,
                    "pedido_anticipado": pedido_anticipado,
                    "creado_en": creado_en,
                },
            )
            return reserva

        def create_pedido(
            *,
            reserva: Reserva,
            plato: Plato,
            cantidad: int,
            estado: str,
            creado_en: datetime,
            fecha_limite: datetime,
            preparado_por: User | None = None,
            preparado_en: datetime | None = None,
            listo_en: datetime | None = None,
            ingredientes_descontados: bool = False,
        ) -> Pedido:
            # Clave determinista para que reruns no dupliquen.
            pedido, _ = Pedido.objects.update_or_create(
                reserva=reserva,
                plato=plato,
                fecha_limite=fecha_limite,
                defaults={
                    "plato_texto": plato.nombre,
                    "cantidad": cantidad,
                    "precio": plato.precio * Decimal(cantidad),
                    "estado": estado,
                    "creado_en": creado_en,
                    "preparado_por": preparado_por,
                    "preparado_en": preparado_en,
                    "listo_en": listo_en,
                    "ingredientes_descontados": ingredientes_descontados,
                },
            )
            return pedido

        def create_pago(
            *,
            reserva: Reserva,
            metodo: str,
            estado: str,
            referencia: str,
            importe: Decimal,
            creado_en: datetime,
        ) -> Pago:
            pago, _ = Pago.objects.update_or_create(
                reserva=reserva,
                referencia=referencia,
                defaults={
                    "metodo": metodo,
                    "estado": estado,
                    "importe": importe,
                    "creado_en": creado_en,
                },
            )
            return pago

        # -------------------------
        # 1) Historico realista (14 dias hasta el 28/05/2026)
        # -------------------------
        reservas_creadas = 0
        pedidos_creados = 0
        pagos_creados = 0

        slots_lunch = [time(13, 30), time(14, 0), time(14, 30), time(15, 0), time(15, 30)]
        slots_dinner = [time(20, 0), time(20, 30), time(21, 0), time(21, 30), time(22, 0)]
        all_slots = slots_lunch + slots_dinner

        for day_offset in range(14):
            d = inicio_14d + timedelta(days=day_offset)
            # mas trafico viernes/sabado/domingo
            weekday = (inicio_14d + timedelta(days=day_offset)).weekday()
            base = 6 if weekday in (4, 5, 6) else 4
            n_reservas = base + rng.randint(0, 4)

            # Control simple de colisiones por mesa/hora
            usados: set[tuple[int, time]] = set()

            for i in range(n_reservas):
                mesa = rng.choice(mesas)
                hora = rng.choice(all_slots)
                guard = 0
                while (mesa.id, hora) in usados and guard < 50:
                    mesa = rng.choice(mesas)
                    hora = rng.choice(all_slots)
                    guard += 1
                usados.add((mesa.id, hora))

                nombre, email = pick_cliente(day_offset * 100 + i)
                creado_en = aware(
                    datetime.combine(d, time(rng.randint(9, 12), rng.choice([0, 15, 30, 45])))
                )
                estado_reserva = rng.choices(
                    [
                        Reserva.ESTADO_CONFIRMADA,
                        Reserva.ESTADO_COMPLETADA,
                        Reserva.ESTADO_CANCELADA,
                    ],
                    weights=[0.60, 0.30, 0.10],
                )[0]

                reserva = get_or_create_reserva(
                    mesa=mesa,
                    fecha=d,
                    hora=hora,
                    nombre_cliente=nombre,
                    email_cliente=email,
                    estado=estado_reserva,
                    pedido_anticipado=True,
                    creado_en=creado_en,
                )
                reservas_creadas += 1

                # pedidos por reserva
                n_pedidos = rng.randint(1, 4)
                elegido = rng.sample(platos, k=min(n_pedidos, len(platos)))
                reserva_dt = aware(datetime.combine(d, hora))
                for plato in elegido:
                    cantidad = rng.choices([1, 2, 3], weights=[0.70, 0.25, 0.05])[0]
                    fecha_limite = reserva_dt - timedelta(minutes=rng.choice([30, 45, 60, 90]))
                    pedido_creado_en = fecha_limite - timedelta(minutes=rng.randint(20, 120))

                    if estado_reserva == Reserva.ESTADO_CANCELADA:
                        estado_pedido = Pedido.ESTADO_PENDIENTE
                        preparado_por = None
                        preparado_en = None
                        listo_en = None
                        ingredientes_descontados = False
                    else:
                        # la mayoria de pedidos del historico quedan entregados
                        estado_pedido = rng.choices(
                            [
                                Pedido.ESTADO_ENTREGADO,
                                Pedido.ESTADO_LISTO,
                                Pedido.ESTADO_PREPARANDO,
                            ],
                            weights=[0.78, 0.15, 0.07],
                        )[0]
                        preparado_por = rng.choice(empleados)
                        preparado_en = fecha_limite - timedelta(minutes=rng.randint(5, 35))
                        duracion_prep = timedelta(minutes=rng.randint(6, 24))
                        listo_en = preparado_en + duracion_prep if estado_pedido in {Pedido.ESTADO_LISTO, Pedido.ESTADO_ENTREGADO} else None
                        ingredientes_descontados = estado_pedido == Pedido.ESTADO_ENTREGADO

                    create_pedido(
                        reserva=reserva,
                        plato=plato,
                        cantidad=cantidad,
                        estado=estado_pedido,
                        creado_en=pedido_creado_en,
                        fecha_limite=fecha_limite,
                        preparado_por=preparado_por,
                        preparado_en=preparado_en,
                        listo_en=listo_en,
                        ingredientes_descontados=ingredientes_descontados,
                    )
                    pedidos_creados += 1

                # pagos asociados (no para canceladas)
                if estado_reserva != Reserva.ESTADO_CANCELADA:
                    importe = sum(
                        (p.precio for p in reserva.pedidos.all()),
                        Decimal("0"),
                    )
                    # pequeñas diferencias "realistas" (propinas/redondeos)
                    if rng.random() < 0.25:
                        importe += Decimal(rng.choice(["0.00", "0.50", "1.00", "1.50", "2.00"]))

                    metodo = rng.choices(
                        [Pago.METODO_LOCAL, Pago.METODO_TARJETA, Pago.METODO_BIZUM],
                        weights=[0.45, 0.40, 0.15],
                    )[0]
                    estado_pago = rng.choices(
                        [Pago.ESTADO_APROBADO, Pago.ESTADO_PENDIENTE, Pago.ESTADO_RECHAZADO],
                        weights=[0.85, 0.08, 0.07],
                    )[0]
                    pago_creado_en = reserva_dt + timedelta(minutes=rng.randint(35, 110))
                    ref_prefix = "TPV" if metodo == Pago.METODO_TARJETA else ("BZM" if metodo == Pago.METODO_BIZUM else "LOC")
                    referencia = f"{ref_prefix}-{d.strftime('%Y%m%d')}-{rng.randint(100000, 999999)}"

                    create_pago(
                        reserva=reserva,
                        metodo=metodo,
                        estado=estado_pago,
                        referencia=referencia,
                        importe=importe.quantize(Decimal("0.01")),
                        creado_en=pago_creado_en,
                    )
                    pagos_creados += 1

        # -------------------------
        # 2) Cola "viva" para el rol empleado (colores por <1h/<2h/<3h/late)
        # -------------------------
        # Reservas cerca del anchor para que el UI muestre diferentes urgencias en la cola.
        cola_specs = [
            # (mesa_idx, hora_reserva, deadline_delta, estado_pedido, empleado_idx, label)
            (0, time(10, 0), timedelta(minutes=-45), Pedido.ESTADO_PENDIENTE, None, "late"),
            (1, time(12, 0), timedelta(minutes=60), Pedido.ESTADO_PENDIENTE, None, "lt1h"),
            (2, time(13, 0), timedelta(minutes=110), Pedido.ESTADO_PENDIENTE, None, "lt2h"),
            (3, time(14, 0), timedelta(minutes=170), Pedido.ESTADO_PENDIENTE, None, "lt3h"),
            (4, time(16, 0), timedelta(minutes=360), Pedido.ESTADO_PENDIENTE, None, "normal"),
            (5, time(12, 30), timedelta(minutes=75), Pedido.ESTADO_PREPARANDO, 0, "preparando A"),
            (0, time(14, 30), timedelta(minutes=150), Pedido.ESTADO_PREPARANDO, 1, "preparando B"),
            (1, time(15, 0), timedelta(minutes=200), Pedido.ESTADO_LISTO, 2, "listo"),
        ]

        reservas_cola = []
        for idx, (mesa_idx, hora_reserva, delta_minutes, estado_pedido, empleado_idx, _) in enumerate(cola_specs):
            mesa = mesas[mesa_idx % len(mesas)]
            nombre, email = pick_cliente(9000 + idx)
            reserva_dt = aware(datetime.combine(anchor_date, hora_reserva))
            reserva = get_or_create_reserva(
                mesa=mesa,
                fecha=anchor_date,
                hora=hora_reserva,
                nombre_cliente=nombre,
                email_cliente=email,
                estado=Reserva.ESTADO_CONFIRMADA,
                pedido_anticipado=True,
                creado_en=anchor - timedelta(days=1, hours=rng.randint(1, 6)),
            )
            reservas_cola.append(reserva)

            plato = rng.choice(platos)
            cantidad = rng.choices([1, 2], weights=[0.8, 0.2])[0]
            fecha_limite = anchor + delta_minutes
            pedido_creado_en = fecha_limite - timedelta(minutes=rng.randint(10, 80))

            preparado_por = None
            preparado_en = None
            listo_en = None
            ingredientes_descontados = False

            if estado_pedido == Pedido.ESTADO_PREPARANDO:
                preparado_por = empleados[empleado_idx % len(empleados)] if empleado_idx is not None else rng.choice(empleados)
                preparado_en = anchor - timedelta(minutes=rng.randint(5, 25))
            elif estado_pedido == Pedido.ESTADO_LISTO:
                preparado_por = empleados[empleado_idx % len(empleados)] if empleado_idx is not None else rng.choice(empleados)
                preparado_en = anchor - timedelta(minutes=rng.randint(25, 55))
                listo_en = anchor - timedelta(minutes=rng.randint(2, 12))

            create_pedido(
                reserva=reserva,
                plato=plato,
                cantidad=cantidad,
                estado=estado_pedido,
                creado_en=pedido_creado_en,
                fecha_limite=fecha_limite,
                preparado_por=preparado_por,
                preparado_en=preparado_en,
                listo_en=listo_en,
                ingredientes_descontados=ingredientes_descontados,
            )
            pedidos_creados += 1

        # Estado actual de mesas: marcar como reservadas las que tienen reservas confirmadas el 28/05.
        mesas_a_reservar = (
            Reserva.objects.filter(fecha=anchor_date)
            .exclude(estado=Reserva.ESTADO_CANCELADA)
            .values_list("mesa_id", flat=True)
            .distinct()
        )
        Mesa.objects.filter(id__in=list(mesas_a_reservar)).update(estado=Mesa.ESTADO_RESERVADA)

        self.stdout.write(self.style.SUCCESS("seed_fastflow3 aplicado."))
        self.stdout.write(
            f"Anchor demo: {anchor.isoformat()} (Europe/Madrid). Ventana historica: {inicio_14d} -> {anchor_date}"
        )
        self.stdout.write(f"Reservas creadas/actualizadas: {reservas_creadas}")
        self.stdout.write(f"Pedidos creados: {pedidos_creados}")
        self.stdout.write(f"Pagos creados: {pagos_creados}")
