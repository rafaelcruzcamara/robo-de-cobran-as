"""Formulários web com validação de dados de clientes e cobranças."""

from django import forms

from cobrancas.models import Cliente, Cobranca, ConfiguracaoRegua


def normalizar_email(email: str) -> str:
    return email.strip().casefold()


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ("nome", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        normalizado = normalizar_email(email)
        for cliente in Cliente.objects.exclude(pk=self.instance.pk):
            if normalizar_email(cliente.email) == normalizado:
                raise forms.ValidationError("Já existe um cliente com este e-mail.")
        return normalizado


class CobrancaForm(forms.ModelForm):
    class Meta:
        model = Cobranca
        fields = ("cliente", "descricao", "valor", "vencimento")
        widgets = {"vencimento": forms.DateInput(attrs={"type": "date"})}

    def clean_descricao(self):
        return self.cleaned_data["descricao"].strip()


class BaixaForm(forms.Form):
    data_baixa = forms.DateField(
        label="Data do pagamento",
        input_formats=("%Y-%m-%d",),
        widget=forms.DateInput(attrs={"type": "date"}),
    )


class ConfiguracaoReguaForm(forms.ModelForm):
    dias_antes = forms.IntegerField(min_value=1, max_value=365, label="Dias antes")
    dias_depois = forms.IntegerField(min_value=1, max_value=365, label="Dias após")

    class Meta:
        model = ConfiguracaoRegua
        fields = ("dias_antes", "dias_depois")
