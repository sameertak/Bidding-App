from django import template

register = template.Library()

@register.filter
def get_value(dictionary, key):
    return dictionary.get(key, '')


@register.filter
def get_value_2(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key, {}).get('amount', '')
    return ''