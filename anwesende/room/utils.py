import django.template as djt

register = djt.Library()
# see https://docs.djangoproject.com/en/stable/howto/custom-template-tags/

ALT_SLASH = '\N{DIVISION SLASH}'


@register.filter
def escape_slash(urlparam: str) -> str:
    """
    Avoid having a slash in the urlparam URL part, 
    because it would not get URL-encoded.
    See https://stackoverflow.com/questions/67849991/django-urls-reverse-url-encoding-the-slash
    Possible replacement characters are
    codepoint   char    utf8    name    oldname
    U+2044 	⁄ 	e2 81 84 	FRACTION SLASH
    U+2215 	∕ 	e2 88 95 	DIVISION SLASH
    U+FF0F 	／ 	ef bc 8f 	FULLWIDTH SOLIDUS 	FULLWIDTH SLASH
    None of them will look quite right if the browser shows the char rather than
    the %-escape in the address line, but DIVISION SLASH comes close.
    The normal slash is
    U+002F 	/ 	2f 	SOLIDUS 	SLASH
    To get back the urlparam after calling escape_slash, 
    the URL will be formed (via {% url ... } or reverse()) and URL-encoded, 
    sent to the browser,
    received by Django in a request, URL-unencoded, split, 
    its param parts handed to a view as args or kwargs,
    and finally unescape_slash will be called by the view.
    """
    return urlparam.replace('/', ALT_SLASH)


def unescape_slash(urlparam_q: str) -> str:
    return urlparam_q.replace(ALT_SLASH, '/')
