import django.core.exceptions as djce


def validate_isprintable(value, message=None):
    if message is None:
        message = "Bitte nur sichtbare Zeichen / Printable characters only"
    if not isinstance(value, str) or not value.isprintable():
        raise djce.ValidationError(message)
