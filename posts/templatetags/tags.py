from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def submitting(context):
    return context.get("submission", False)


@register.simple_tag(takes_context=True)
def exists(context, arg):
    v = context.get(arg)
    if v is not None:
        return True
    return False
