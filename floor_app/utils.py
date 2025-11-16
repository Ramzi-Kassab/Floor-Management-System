from django.core.exceptions import ValidationError


def require_if(flag_field: str, value_field: str, message: str):
    def _clean(instance):
        if getattr(instance, flag_field) and (getattr(instance, value_field) in (None, '', 0)):
            raise ValidationError({value_field: message})
    return _clean


def get_client_ip(request):
    if not request:
        return None
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")

