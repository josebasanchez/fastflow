from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("restaurante", "0003_rename_restaurante_status_next_idx_restaurante_status_cc1b1a_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="pedido",
            name="listo_en",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="pedido",
            name="preparado_en",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="pedido",
            name="preparado_por",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="pedidos_preparados", to=settings.AUTH_USER_MODEL),
        ),
    ]
