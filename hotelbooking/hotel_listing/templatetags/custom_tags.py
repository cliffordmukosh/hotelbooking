from django import template

register = template.Library()

@register.filter
def to(start, end):
    """
    Custom filter to generate a range in templates.
    Usage: {% for i in 1|to:10 %}
    """
    return range(start, end + 1)
