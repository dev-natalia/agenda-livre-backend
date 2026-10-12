from django import forms
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile

from apps.activities.images import process_image
from apps.activities.models import Activity


class ActivityAdminForm(forms.ModelForm):
    """Formulário da atividade no Admin: valida e trata a imagem recém-enviada."""

    # `FileField` e não `ImageField`: assim só `process_image` valida o arquivo e as mensagens
    # são sempre as do contrato (a validação padrão do Django devolveria outro texto).
    image = forms.FileField(label="Imagem", required=False, widget=forms.ClearableFileInput)

    class Meta:
        model = Activity
        fields = "__all__"

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if not isinstance(image, UploadedFile):
            return image  # sem envio novo: arquivo atual, vazio ou pedido de limpeza
        processed, extension = process_image(image)
        return ContentFile(processed.read(), name=f"imagem.{extension}")
