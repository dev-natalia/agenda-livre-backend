from apps.activities.models import Activity

Status = Activity.Status

ALLOWED_TRANSITIONS = {
    Status.DRAFT: {Status.PUBLISHED},
    Status.PUBLISHED: {Status.CANCELLED, Status.FINISHED},
    Status.CANCELLED: {Status.PUBLISHED},
    Status.FINISHED: {Status.PUBLISHED},
}


class StatusChangeError(Exception):
    """Mudança de situação recusada; a mensagem é exibida à pessoa administradora."""


def validate_publication(activity):
    if not activity.title.strip():
        raise StatusChangeError("Falta o título.")
    if not activity.description.strip():
        raise StatusChangeError("Falta a descrição.")
    if not activity.unit.is_active:
        raise StatusChangeError("A unidade está inativa.")
    if not activity.category.is_active:
        raise StatusChangeError("A categoria está inativa.")
    if not activity.audience_links.exists():
        raise StatusChangeError("Falta ao menos um público-alvo.")


def change_status(activity, new_status, user):
    """Muda a situação da atividade. Devolve False se ela já estava na situação pedida."""
    if activity.status == new_status:
        return False
    if new_status not in ALLOWED_TRANSITIONS.get(activity.status, set()):
        current = Status(activity.status).label
        target = Status(new_status).label
        raise StatusChangeError(f"Não é possível passar de {current} para {target}.")
    if new_status == Status.PUBLISHED:
        validate_publication(activity)
    activity.status = new_status
    activity.updated_by = user
    activity.save(update_fields=["status", "updated_by", "updated_at"])
    return True
