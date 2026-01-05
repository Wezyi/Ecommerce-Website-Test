"""
URL configuration for setup project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from produtos.views import home, detalhe_produto, adicionar_ao_carrinho, ver_carrinho, remover_do_carrinho, atualizar_quantidade_carrinho
from django.conf import settings
from django.conf.urls.static import static
from produtos import views as store_views
from core import views as core_views

urlpatterns = [
    path('admin_wilson/', admin.site.urls),
    path('contas/', include('contas.urls')), # Adiciona isto
    path('', home, name='home'),
    path('produto/<int:id>/', detalhe_produto, name='detalhe_produto'),
    # Novas rotas do Carrinho:
    path('carrinho/adicionar/<int:produto_id>/', store_views.adicionar_ao_carrinho, name='adicionar_ao_carrinho'),
    path('carrinho/', store_views.ver_carrinho, name='ver_carrinho'),
    path('carrinho/remover/<int:produto_id>/', remover_do_carrinho, name='remover_do_carrinho'),
    path('carrinho/atualizar/<int:produto_id>/', atualizar_quantidade_carrinho, name='atualizar_quantidade_carrinho'),
    path('pagamento/criar/', store_views.criar_pagamento, name='criar_pagamento'),
    path('pagamento/sucesso/', store_views.pagamento_sucesso, name='pagamento_sucesso'),
    path('pagamento/cancelar/', store_views.pagamento_cancelar, name='pagamento_cancelar'),
    path('checkout/', store_views.checkout, name='checkout'),
    path('checkout/processar/', store_views.processar_checkout, name='processar_checkout'),
    path('minhas-encomendas/', store_views.minhas_encomendas, name='minhas_encomendas'),
    path('pesquisa/', store_views.pesquisa, name='pesquisa'),
    path('aplicar-cupom/', store_views.aplicar_cupom, name='aplicar_cupom'),
    path('sobre/', core_views.sobre, name='sobre'),
    path('contactos/', core_views.contacto, name='contacto'),
    path('privacidade/', core_views.politica_privacidade, name='privacidade'),
    path('termos/', core_views.termos_condicoes, name='termos'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
