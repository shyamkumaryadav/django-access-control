from .models import UserOrgRole


def is_superuser(user):
    return bool(user and user.is_authenticated and user.is_superuser)


def is_org_admin(user, org):
    if not user or not user.is_authenticated:
        return False

    if not org:
        return False

    return org.admin_id == user.id


def get_user_org_role(user, org):
    """
    Return user's role inside one org.

    Possible return values:
    - "PI"
    - "READ_ONLY"
    - None
    """

    if not user or not user.is_authenticated:
        return None

    if not org:
        return None

    if user.is_superuser:
        return None

    if org.admin_id == user.id:
        return None

    return (
        UserOrgRole.objects.filter(user=user, org=org)
        .values_list("role", flat=True)
        .first()
    )
