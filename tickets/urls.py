from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('cadastro/', views.cadastro_view, name='cadastro'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('detalhes/<int:id>/', views.detalhes_view, name='detalhes'),
    path('criar/', views.criar_view, name='criar'),
    path('logout/', views.logout_view, name='logout'),
    path('deletar-anexo/<int:chamado_id>/<int:anexo_id>/', views.deletar_anexo, name='deletar_anexo'),
]