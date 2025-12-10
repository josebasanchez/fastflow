from django.contrib import admin
from .models import Mesa, Reserva, Pedido, Usuario

admin.site.register(Mesa)
admin.site.register(Reserva)
admin.site.register(Pedido)
admin.site.register(Usuario)
