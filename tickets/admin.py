from django.contrib import admin
from .models import Perfil, Chamado # Importa seus modelos

# Registra o Perfil para aparecer no Admin
admin.site.register(Perfil)

# Aproveite e registre os Chamados também se não tiver feito
admin.site.register(Chamado)