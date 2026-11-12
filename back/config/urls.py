"""Rotas principais da aplicação."""

from django.urls import include, path

from cobrancas import views

urlpatterns = [
    path("accounts/", include("django.contrib.auth.urls")),
    path("", views.painel, name="dashboard"),
    path("regua/", views.configurar_regua, name="configurar_regua"),
    path("clientes/", views.lista_clientes, name="lista_clientes"),
    path("clientes/novo/", views.criar_cliente, name="criar_cliente"),
    path("clientes/<int:cliente_id>/", views.detalhe_cliente, name="detalhe_cliente"),
    path(
        "clientes/<int:cliente_id>/pausar/", views.alternar_pausa, name="alternar_pausa"
    ),
    path("cobrancas/", views.lista_cobrancas, name="lista_cobrancas"),
    path("cobrancas/nova/", views.criar_cobranca, name="criar_cobranca"),
    path(
        "cobrancas/<int:cobranca_id>/", views.detalhe_cobranca, name="detalhe_cobranca"
    ),
    path(
        "cobrancas/<int:cobranca_id>/baixar/",
        views.baixar_cobranca,
        name="baixar_cobranca",
    ),
    path("importar/", views.importar_cobrancas, name="importar_cobrancas"),
]
