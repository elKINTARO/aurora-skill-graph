from django import template
from django.utils.safestring import mark_safe
import markdown as md

register = template.Library()

@register.filter(name='markdown')
def markdown_format(text):
    if not text:
        return ""

    html = md.markdown(text, extensions=['fenced_code', 'nl2br'])

    return mark_safe(html)