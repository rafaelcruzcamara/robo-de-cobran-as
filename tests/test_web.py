import re
from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import Client
from django.urls import reverse

from cobrancas.models import Cliente, Cobranca, ConfiguracaoRegua

CSV_VALIDO = (
    "cliente;email;descricao;valor;vencimento;pago;pausado\n"
    "Ana;ana@example.com;Mensalidade;125,90;20/11/2026;não;não\n"
)


def usuario_autenticado(client=None):
    user = get_user_model().objects.create_user(
        username="operador", password="senha-de-teste"
    )
    cliente = client or Client()
    cliente.force_login(user)
    return cliente


def csv_upload(conteudo=CSV_VALIDO, nome="cobrancas.csv"):
    return SimpleUploadedFile(nome, conteudo.encode("utf-8"), content_type="text/csv")


def test_views_de_dados_exigem_login():
    client = Client()

    for url in (
        reverse("dashboard"),
        reverse("lista_clientes"),
        reverse("lista_cobrancas"),
        reverse("importar_cobrancas"),
        reverse("configurar_regua"),
    ):
        resposta = client.get(url)
        assert resposta.status_code == 302
        assert resposta.url.startswith(reverse("login"))


def test_login_com_credenciais_validas_redireciona_ao_painel():
    get_user_model().objects.create_user(username="operador", password="senha-de-teste")
    client = Client()

    resposta = client.post(
        reverse("login"), {"username": "operador", "password": "senha-de-teste"}
    )

    assert resposta.status_code == 302
    assert resposta.url == reverse("dashboard")
    assert client.get(reverse("dashboard")).status_code == 200


def test_login_exibe_painel_com_totais_e_conteudo_escapado():
    client = usuario_autenticado()
    pessoa = Cliente.objects.create(
        nome="<script>alert(1)</script>", email="a@example.com"
    )
    Cobranca.objects.create(
        cliente=pessoa,
        descricao="Mensalidade",
        valor=Decimal("125.90"),
        vencimento=date(2020, 1, 1),
    )

    resposta = client.get(reverse("dashboard"))

    assert resposta.status_code == 200
    assert "R$ 125,90" in resposta.content.decode()
    detalhe = client.get(reverse("detalhe_cliente", args=[pessoa.pk]))
    conteudo = detalhe.content.decode()
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in conteudo
    assert "<script>alert(1)</script>" not in conteudo


def test_cria_cliente_com_email_normalizado_e_rejeita_duplicado():
    client = usuario_autenticado()
    url = reverse("criar_cliente")

    resposta = client.post(url, {"nome": "Ana", "email": "  ANA@example.com "})

    assert resposta.status_code == 302
    assert Cliente.objects.get().email == "ana@example.com"
    resposta = client.post(url, {"nome": "Outra Ana", "email": "ana@EXAMPLE.com"})
    assert resposta.status_code == 200
    assert Cliente.objects.count() == 1


def test_banco_impede_email_duplicado_mesmo_por_outra_escrita():
    Cliente.objects.create(nome="Ana", email="ana@example.com")

    with pytest.raises(IntegrityError), transaction.atomic():
        Cliente.objects.create(nome="Outra Ana", email=" ANA@example.com ")


def test_pausa_e_baixa_sao_acoes_post_e_alteram_a_regra():
    client = usuario_autenticado()
    cliente = Cliente.objects.create(nome="Ana", email="ana@example.com")
    cobranca = Cobranca.objects.create(
        cliente=cliente,
        descricao="Mensalidade",
        valor=Decimal("125.90"),
        vencimento=date(2026, 11, 20),
    )

    pausa = client.post(reverse("alternar_pausa", args=[cliente.pk]))
    assert pausa.status_code == 302
    cliente.refresh_from_db()
    assert cliente.pausado is True
    assert client.get(reverse("alternar_pausa", args=[cliente.pk])).status_code == 405

    baixa = client.post(
        reverse("baixar_cobranca", args=[cobranca.pk]),
        {"data_baixa": "2026-11-18"},
    )
    assert baixa.status_code == 302
    cobranca.refresh_from_db()
    assert cobranca.baixada_em == date(2026, 11, 18)
    assert cobranca.paga is True


def test_cadastra_cobranca_e_rejeita_valor_nao_positivo():
    client = usuario_autenticado()
    pessoa = Cliente.objects.create(nome="Ana", email="ana@example.com")
    url = reverse("criar_cobranca")
    dados = {
        "cliente": pessoa.pk,
        "descricao": "Mensalidade",
        "valor": "125.90",
        "vencimento": "2026-11-20",
    }

    resposta = client.post(url, dados)

    assert resposta.status_code == 302
    assert Cobranca.objects.get().valor == Decimal("125.90")
    dados["valor"] = "0"
    resposta = client.post(url, dados)
    assert resposta.status_code == 200
    assert Cobranca.objects.count() == 1
    dados.update(valor="125.90", descricao="  MENSALIDADE  ")
    resposta = client.post(url, dados)
    assert resposta.status_code == 200
    assert Cobranca.objects.count() == 1


def test_configura_intervalos_da_regua_com_validacao():
    client = usuario_autenticado()
    url = reverse("configurar_regua")

    previa = client.get(url)
    assert previa.status_code == 200
    assert 'value="2"' in previa.content.decode()
    assert 'value="7"' in previa.content.decode()

    resposta = client.post(url, {"dias_antes": "3", "dias_depois": "10"})
    assert resposta.status_code == 302
    configuracao = ConfiguracaoRegua.objects.get(pk=1)
    assert (configuracao.dias_antes, configuracao.dias_depois) == (3, 10)

    resposta = client.post(url, {"dias_antes": "0", "dias_depois": "10"})
    configuracao.refresh_from_db()
    assert resposta.status_code == 200
    assert (configuracao.dias_antes, configuracao.dias_depois) == (3, 10)


def test_importacao_exige_revisao_e_confirma_em_transacao():
    client = usuario_autenticado()
    url = reverse("importar_cobrancas")

    previa = client.post(url, {"arquivo": csv_upload()})

    assert previa.status_code == 200
    assert "Nenhuma foi gravada ainda" in previa.content.decode()
    assert Cliente.objects.count() == 0
    assert Cobranca.objects.count() == 0

    token = re.search(
        r'name="token_confirmacao" value="([^"]+)"', previa.content.decode()
    ).group(1)
    confirmacao = client.post(
        url,
        {
            "arquivo": csv_upload(),
            "confirmar": "1",
            "token_confirmacao": token,
        },
    )

    assert confirmacao.status_code == 302
    assert Cliente.objects.get().email == "ana@example.com"
    assert Cobranca.objects.get().valor == Decimal("125.90")


def test_importacao_preserva_pago_sem_inventar_data_de_baixa():
    client = usuario_autenticado()
    url = reverse("importar_cobrancas")
    conteudo = CSV_VALIDO.replace("não;não", "sim;sim")
    previa = client.post(url, {"arquivo": csv_upload(conteudo)})
    token = re.search(
        r'name="token_confirmacao" value="([^"]+)"', previa.content.decode()
    ).group(1)

    resposta = client.post(
        url,
        {
            "arquivo": csv_upload(conteudo),
            "confirmar": "1",
            "token_confirmacao": token,
        },
    )

    assert resposta.status_code == 302
    pessoa = Cliente.objects.get()
    cobranca = Cobranca.objects.get()
    assert pessoa.pausado is True
    assert cobranca.paga is True
    assert cobranca.baixada_em is None


def test_importacao_reutiliza_cliente_sem_alterar_nome_ou_pausa():
    client = usuario_autenticado()
    pessoa = Cliente.objects.create(
        nome="Nome salvo", email="ana@example.com", pausado=True
    )
    conteudo = CSV_VALIDO.replace("Ana;ana@example.com", "Outro nome;ANA@example.com")
    conteudo = conteudo.replace("Mensalidade", "Serviço extra")
    previa = client.post(
        reverse("importar_cobrancas"), {"arquivo": csv_upload(conteudo)}
    )
    token = re.search(
        r'name="token_confirmacao" value="([^"]+)"', previa.content.decode()
    ).group(1)

    resposta = client.post(
        reverse("importar_cobrancas"),
        {
            "arquivo": csv_upload(conteudo),
            "confirmar": "1",
            "token_confirmacao": token,
        },
    )

    assert resposta.status_code == 302
    assert Cliente.objects.count() == 1
    pessoa.refresh_from_db()
    assert pessoa.nome == "Nome salvo"
    assert pessoa.pausado is True
    assert Cobranca.objects.count() == 1


def test_confirmacao_nao_grava_arquivo_diferente_da_previa():
    client = usuario_autenticado()
    url = reverse("importar_cobrancas")
    previa = client.post(url, {"arquivo": csv_upload()})
    token = re.search(
        r'name="token_confirmacao" value="([^"]+)"', previa.content.decode()
    ).group(1)
    arquivo_alterado = CSV_VALIDO.replace("125,90", "225,90")

    resposta = client.post(
        url,
        {
            "arquivo": csv_upload(arquivo_alterado),
            "confirmar": "1",
            "token_confirmacao": token,
        },
    )

    assert resposta.status_code == 200
    assert "arquivo mudou desde a prévia" in resposta.content.decode()
    assert Cliente.objects.count() == 0
    assert Cobranca.objects.count() == 0


def test_importacao_invalida_ou_duplicada_nao_grava_nada():
    client = usuario_autenticado()
    url = reverse("importar_cobrancas")
    duplicada = (
        CSV_VALIDO + "Ana;ana@example.com;Mensalidade;125,90;20/11/2026;não;não\n"
    )

    resposta = client.post(url, {"arquivo": csv_upload(duplicada)})

    assert resposta.status_code == 200
    assert "possível cobrança duplicada" in resposta.content.decode()
    assert Cliente.objects.count() == 0
    assert Cobranca.objects.count() == 0

    resposta = client.post(url, {"arquivo": csv_upload("cliente;email\nAna;invalido")})
    assert resposta.status_code == 200
    assert Cliente.objects.count() == 0
    assert Cobranca.objects.count() == 0


def test_importacao_rejeita_duplicata_existente_sem_alterar_cliente():
    client = usuario_autenticado()
    pessoa = Cliente.objects.create(
        nome="Nome original", email="ana@example.com", pausado=True
    )
    Cobranca.objects.create(
        cliente=pessoa,
        descricao="Mensalidade",
        valor=Decimal("125.90"),
        vencimento=date(2026, 11, 20),
    )

    resposta = client.post(reverse("importar_cobrancas"), {"arquivo": csv_upload()})

    assert resposta.status_code == 200
    assert "possível cobrança duplicada" in resposta.content.decode()
    assert Cliente.objects.count() == 1
    pessoa.refresh_from_db()
    assert pessoa.nome == "Nome original"
    assert pessoa.pausado is True
    assert Cobranca.objects.count() == 1


def test_importacao_limita_tamanho_do_arquivo():
    client = usuario_autenticado()
    arquivo_grande = SimpleUploadedFile(
        "grande.csv", b"x" * (5 * 1024 * 1024 + 1), content_type="text/csv"
    )

    resposta = client.post(reverse("importar_cobrancas"), {"arquivo": arquivo_grande})

    assert resposta.status_code == 200
    assert "excede 5 MB" in resposta.content.decode()
    assert Cliente.objects.count() == 0
    assert Cobranca.objects.count() == 0


def test_post_sem_csrf_e_bloqueado():
    client = Client(enforce_csrf_checks=True)
    login = client.get(reverse("login"))
    assert login.status_code == 200

    resposta = client.post(
        reverse("login"), {"username": "operador", "password": "senha"}
    )

    assert resposta.status_code == 403
