from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import PerfilUsuario


@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance: User, created: bool, **kwargs):
    """
    Ensure every User has a PerfilUsuario.

    Some users are created outside the API serializer (admin, fixtures, seeds).
    This keeps the invariant consistent across the app.
    """
    if hasattr(instance, "perfil"):
        return
    PerfilUsuario.objects.get_or_create(user=instance)
