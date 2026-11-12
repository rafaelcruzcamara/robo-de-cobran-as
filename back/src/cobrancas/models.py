"""Modelos persistentes de clientes, cobranças e histórico de etapas."""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F
from django.db.models.functions import Lower, Trim


class Cliente(models.Model):
    nome = models.CharField(max_length=200)
    email = models.EmailField(max_length=254)
    pausado = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.nome

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower(Trim("email")), name="cliente_email_normalizado_unico"
            )
        ]


class Cobranca(models.Model):
    cliente = models.ForeignKey(
        Cliente, on_delete=models.PROTECT, related_name="cobrancas"
    )
    descricao = models.CharField(max_length=200)
    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    vencimento = models.DateField()
    paga = models.BooleanField(default=False)
    baixada_em = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.baixada_em:
            self.paga = True
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.descricao} — {self.cliente.nome}"

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(baixada_em__isnull=True) | models.Q(paga=True),
                name="cobranca_com_data_baixa_esta_paga",
            ),
            models.UniqueConstraint(
                F("cliente"),
                Lower(Trim("descricao")),
                F("valor"),
                F("vencimento"),
                name="cobranca_cliente_descricao_valor_data_unica",
            ),
        ]


class HistoricoEtapa(models.Model):
    class Etapa(models.TextChoices):
        PRE_VENCIMENTO = "pre_vencimento", "Pré-vencimento"
        VENCIMENTO = "vencimento", "No vencimento"
        ATRASO_7_DIAS = "atraso_7_dias", "Pós-vencimento"

    class Estado(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        ENVIANDO = "enviando", "Em envio"
        ENVIADO = "enviado", "Enviado"
        FALHOU = "falhou", "Falhou"

    cobranca = models.ForeignKey(
        Cobranca, on_delete=models.PROTECT, related_name="historico_etapas"
    )
    etapa = models.CharField(max_length=32, choices=Etapa.choices)
    data_execucao = models.DateField()
    estado = models.CharField(
        max_length=16, choices=Estado.choices, default=Estado.PENDENTE
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    @property
    def descricao_etapa(self) -> str:
        dias_ate_vencimento = (self.cobranca.vencimento - self.data_execucao).days
        if self.etapa == self.Etapa.PRE_VENCIMENTO:
            return f"Pré-vencimento ({dias_ate_vencimento} dias)"
        if self.etapa == self.Etapa.ATRASO_7_DIAS:
            return f"Pós-vencimento ({abs(dias_ate_vencimento)} dias)"
        return "No vencimento"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("cobranca", "etapa"), name="unica_etapa_por_cobranca"
            )
        ]


class ConfiguracaoRegua(models.Model):
    """Parâmetros globais para as duas etapas relativas ao vencimento."""

    dias_antes = models.PositiveSmallIntegerField(default=2)
    dias_depois = models.PositiveSmallIntegerField(default=7)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(dias_antes__gte=1, dias_antes__lte=365)
                    & models.Q(dias_depois__gte=1, dias_depois__lte=365)
                ),
                name="intervalos_regua_entre_1_e_365",
            )
        ]
