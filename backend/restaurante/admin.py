from django.contrib import admin

from .models import Ingrediente, Mesa, Pago, Pedido, PerfilUsuario, Plato, Receta, Reserva


admin.site.register(PerfilUsuario)
admin.site.register(Mesa)
admin.site.register(Reserva)
admin.site.register(Pedido)
admin.site.register(Pago)
admin.site.register(Ingrediente)
admin.site.register(Plato)
admin.site.register(Receta)
