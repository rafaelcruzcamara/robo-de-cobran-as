"""Páginas autenticadas para a operação do robô de cobrança."""

import hashlib
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.core.paginator import Paginator
from django.core.signing import BadSignature
from django.db import IntegrityError, transaction
from django.db.models import Q, Sum
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from cobrancas.forms import (
    BaixaForm,
    ClienteForm,
    CobrancaForm,
    ConfiguracaoReguaForm,
    normalizar_email,
)
from cobrancas.importacao import ResultadoImportacao, ler_csv, ler_xlsx
from cobrancas.models import Cliente, Cobranca, ConfiguracaoRegua, HistoricoEtapa

_LIMITE_UPLOAD = 5 * 1024 * 1024


@login_required
def painel(request: HttpRequest) -> HttpResponse:
    hoje = timezone.localdate()
    totais = Cobranca.objects.aggregate(
        em_aberto=Sum("valor", filter=Q(paga=False)),
        vencido=Sum("valor", filter=Q(paga=False, vencimento__lt=hoje)),
    )
    contexto = {
        "hoje": hoje,
        "total_em_aberto": totais["em_aberto"] or Decimal("0.00"),
        "total_vencido": totais["vencido"] or Decimal("0.00"),
        "etapas_recentes": HistoricoEtapa.objects.select_related(
            "cobranca__cliente"
        ).order_by("-criado_em")[:10],
    }
    return render(request, "cobrancas/painel.html", contexto)


@login_required
def configurar_regua(request: HttpRequest) -> HttpResponse:
    configuracao, _ = ConfiguracaoRegua.objects.get_or_create(pk=1)
    form = ConfiguracaoReguaForm(request.POST or None, instance=configuracao)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Régua de cobrança atualizada.")
        return redirect("configurar_regua")
    return render(request, "cobrancas/configurar_regua.html", {"form": form})


@login_required
def lista_clientes(request: HttpRequest) -> HttpResponse:
    pagina = Paginator(Cliente.objects.order_by("nome", "id"), 25).get_page(
        request.GET.get("pagina")
    )
    return render(request, "cobrancas/lista_clientes.html", {"pagina": pagina})


@login_required
def criar_cliente(request: HttpRequest) -> HttpResponse:
    form = ClienteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                cliente = form.save()
        except IntegrityError:
            form.add_error("email", "Já existe um cliente com este e-mail.")
        else:
            messages.success(request, "Cliente cadastrado.")
            return redirect("detalhe_cliente", cliente_id=cliente.pk)
    return render(
        request,
        "cobrancas/formulario.html",
        {"form": form, "titulo": "Novo cliente", "voltar": "lista_clientes"},
    )


@login_required
def detalhe_cliente(request: HttpRequest, cliente_id: int) -> HttpResponse:
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    cobrancas = cliente.cobrancas.order_by("paga", "vencimento", "id")
    return render(
        request,
        "cobrancas/detalhe_cliente.html",
        {"cliente": cliente, "cobrancas": cobrancas},
    )


@login_required
def alternar_pausa(request: HttpRequest, cliente_id: int) -> HttpResponse:
    if request.method != "POST":
        return HttpResponse(status=405)
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    cliente.pausado = not cliente.pausado
    cliente.save(update_fields=("pausado",))
    messages.success(
        request,
        "Cliente pausado." if cliente.pausado else "Cliente retomado.",
    )
    return redirect("detalhe_cliente", cliente_id=cliente.pk)


@login_required
def lista_cobrancas(request: HttpRequest) -> HttpResponse:
    busca = request.GET.get("q", "").strip()
    cobrancas = Cobranca.objects.select_related("cliente").order_by(
        "paga", "vencimento", "id"
    )
    if busca:
        cobrancas = cobrancas.filter(
            Q(cliente__nome__icontains=busca) | Q(descricao__icontains=busca)
        )
    pagina = Paginator(cobrancas, 25).get_page(request.GET.get("pagina"))
    return render(
        request,
        "cobrancas/lista_cobrancas.html",
        {"pagina": pagina, "busca": busca},
    )


@login_required
def criar_cobranca(request: HttpRequest) -> HttpResponse:
    form = CobrancaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                cobranca = form.save()
        except IntegrityError:
            form.add_error(
                None,
                "Já existe cobrança deste cliente com a mesma descrição, "
                "valor e vencimento.",
            )
        else:
            messages.success(request, "Cobrança cadastrada.")
            return redirect("detalhe_cobranca", cobranca_id=cobranca.pk)
    return render(
        request,
        "cobrancas/formulario.html",
        {"form": form, "titulo": "Nova cobrança", "voltar": "lista_cobrancas"},
    )


@login_required
def detalhe_cobranca(request: HttpRequest, cobranca_id: int) -> HttpResponse:
    cobranca = get_object_or_404(
        Cobranca.objects.select_related("cliente"), pk=cobranca_id
    )
    historico = cobranca.historico_etapas.order_by("data_execucao", "id")
    return render(
        request,
        "cobrancas/detalhe_cobranca.html",
        {"cobranca": cobranca, "historico": historico},
    )


@login_required
def baixar_cobranca(request: HttpRequest, cobranca_id: int) -> HttpResponse:
    cobranca = get_object_or_404(Cobranca, pk=cobranca_id)
    if cobranca.paga:
        messages.info(request, "Esta cobrança já está baixada.")
        return redirect("detalhe_cobranca", cobranca_id=cobranca.pk)
    form = BaixaForm(request.POST or None, initial={"data_baixa": timezone.localdate()})
    if request.method == "POST" and form.is_valid():
        cobranca.paga = True
        cobranca.baixada_em = form.cleaned_data["data_baixa"]
        cobranca.save(update_fields=("paga", "baixada_em"))
        messages.success(request, "Pagamento registrado.")
        return redirect("detalhe_cobranca", cobranca_id=cobranca.pk)
    return render(
        request,
        "cobrancas/baixar.html",
        {"cobranca": cobranca, "form": form},
    )


def _ler_upload(arquivo) -> tuple[ResultadoImportacao, str | None]:
    if arquivo.size > _LIMITE_UPLOAD:
        return ResultadoImportacao((), ()), None
    extensao = Path(arquivo.name).suffix.casefold()
    conteudo = arquivo.read()
    digest = hashlib.sha256(conteudo).hexdigest()
    if extensao == ".csv":
        try:
            resultado = ler_csv(conteudo.decode("utf-8-sig"))
        except UnicodeDecodeError:
            resultado = ResultadoImportacao((), ())
    elif extensao == ".xlsx":
        resultado = ler_xlsx(conteudo)
    else:
        resultado = ResultadoImportacao((), ())
    return resultado, digest


def _validar_duplicatas(cobrancas) -> list[tuple[int, str]]:
    clientes_por_email: dict[str, list[Cliente]] = defaultdict(list)
    for cliente in Cliente.objects.all():
        clientes_por_email[normalizar_email(cliente.email)].append(cliente)

    chaves_existentes = set()
    for cobranca in Cobranca.objects.select_related("cliente"):
        chaves_existentes.add(
            (
                normalizar_email(cobranca.cliente.email),
                cobranca.descricao.strip().casefold(),
                cobranca.valor,
                cobranca.vencimento,
            )
        )

    erros: list[tuple[int, str]] = []
    vistas = set(chaves_existentes)
    nomes_por_email: dict[str, str] = {}
    for numero, cobranca in enumerate(cobrancas, start=2):
        email = normalizar_email(cobranca.email)
        if len(clientes_por_email[email]) > 1:
            erros.append(
                (numero, "mais de um cliente possui este e-mail; revise os dados")
            )
            continue
        nome_normalizado = cobranca.cliente.strip().casefold()
        if email in nomes_por_email and nomes_por_email[email] != nome_normalizado:
            erros.append(
                (numero, "o mesmo e-mail aparece com nomes diferentes no arquivo")
            )
            continue
        nomes_por_email[email] = nome_normalizado
        chave = (
            email,
            cobranca.descricao.strip().casefold(),
            cobranca.valor,
            cobranca.vencimento,
        )
        if chave in vistas:
            erros.append(
                (numero, "possível cobrança duplicada; arquivo não será importado")
            )
        else:
            vistas.add(chave)
    return erros


@login_required
def importar_cobrancas(request: HttpRequest) -> HttpResponse:
    resultado = None
    erros_extras: list[tuple[int, str]] = []
    token_confirmacao = ""
    arquivo = request.FILES.get("arquivo") if request.method == "POST" else None
    confirmar = (
        request.POST.get("confirmar") == "1" if request.method == "POST" else False
    )

    if request.method == "POST":
        if arquivo is None:
            erros_extras.append(
                (0, "selecione novamente o arquivo para revisar ou confirmar")
            )
        else:
            resultado, digest = _ler_upload(arquivo)
            if not resultado.cobrancas and not resultado.erros:
                mensagem = (
                    "o arquivo excede 5 MB"
                    if arquivo.size > _LIMITE_UPLOAD
                    else "arquivo CSV/XLSX inválido ou extensão não suportada"
                )
                erros_extras.append((0, mensagem))
            erros_extras.extend(_validar_duplicatas(resultado.cobrancas))
            if (
                confirmar
                and resultado.cobrancas
                and not resultado.erros
                and not erros_extras
            ):
                try:
                    digest_previo = signing.loads(
                        request.POST.get("token_confirmacao", ""),
                        salt="cobrancas-importacao-preview",
                        max_age=900,
                    )
                except BadSignature:
                    erros_extras.append(
                        (0, "prévia expirada ou inválida; revise o arquivo novamente")
                    )
                else:
                    if digest_previo != digest:
                        erros_extras.append(
                            (0, "o arquivo mudou desde a prévia; revise-o novamente")
                        )
            if (
                confirmar
                and digest
                and resultado.cobrancas
                and not resultado.erros
                and not erros_extras
            ):
                try:
                    with transaction.atomic():
                        clientes: dict[str, Cliente] = {}
                        for registro in resultado.cobrancas:
                            email = normalizar_email(registro.email)
                            cliente = clientes.get(email)
                            if cliente is None:
                                encontrados = list(
                                    Cliente.objects.filter(email__iexact=email)[:2]
                                )
                                if len(encontrados) > 1:
                                    raise ValueError(
                                        "mais de um cliente possui o mesmo e-mail"
                                    )
                                cliente = (
                                    encontrados[0]
                                    if encontrados
                                    else Cliente.objects.create(
                                        nome=registro.cliente.strip(),
                                        email=email,
                                        pausado=registro.pausada,
                                    )
                                )
                                clientes[email] = cliente
                            Cobranca.objects.create(
                                cliente=cliente,
                                descricao=registro.descricao.strip(),
                                valor=registro.valor,
                                vencimento=registro.vencimento,
                                paga=registro.paga,
                            )
                except (IntegrityError, ValueError):
                    erros_extras.append(
                        (0, "não foi possível confirmar; nenhum registro foi importado")
                    )
                else:
                    messages.success(
                        request,
                        f"Importação concluída: {len(resultado.cobrancas)} cobranças.",
                    )
                    return redirect("lista_cobrancas")
            elif (
                not confirmar
                and digest
                and resultado.cobrancas
                and not resultado.erros
                and not erros_extras
            ):
                token_confirmacao = signing.dumps(
                    digest, salt="cobrancas-importacao-preview"
                )

    return render(
        request,
        "cobrancas/importar.html",
        {
            "resultado": resultado,
            "erros_extras": erros_extras,
            "token_confirmacao": token_confirmacao,
        },
    )
