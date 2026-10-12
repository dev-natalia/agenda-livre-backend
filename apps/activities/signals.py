from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from apps.activities.images import delete_stored_file
from apps.activities.models import Activity


@receiver(post_delete, sender=Activity)
def delete_image_file(sender, instance, **kwargs):
    """Ao excluir a atividade, apaga o arquivo da imagem depois do commit."""
    if instance.image:
        name = instance.image.name
        transaction.on_commit(lambda: delete_stored_file(name))
