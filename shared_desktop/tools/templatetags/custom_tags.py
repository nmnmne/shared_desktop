from django import template


register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(f"group{key}", "")


@register.filter
def get_phase(dictionary, key):
    return dictionary.get(f"phases{key}", "")


@register.filter
def is_primary_group_selected(dictionary, key):
    return dictionary.get("primary_group") == f"group{key}"

@register.filter(name='startswith')
def startswith(value, arg):
    return value.startswith(arg)
