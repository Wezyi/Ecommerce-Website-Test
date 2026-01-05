from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Login (Usa a view pronta do Django)
    path('login/', auth_views.LoginView.as_view(template_name='contas/login.html'), name='login'),
    
    # Logout (Usa a view pronta do Django)
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Registo (Vamos criar esta view no próximo passo)
    path('registo/', views.registo, name='registo'),
    # Editar perfil
    path('perfil/', views.editar_perfil, name='editar_perfil'), # Nova rota
]