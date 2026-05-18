from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from restaurante.models import PerfilUsuario


class Command(BaseCommand):
    help = "Crea PerfilUsuario para cualquier User que no lo tenga."

    def handle(self, *args, **options):
        created_count = 0
        for user in User.objects.all().only("id"):
            _, created = PerfilUsuario.objects.get_or_create(user=user)
            if created:
                created_count += 1
        self.stdout.write(self.style.SUCCESS(f"Perfiles creados: {created_count}"))

