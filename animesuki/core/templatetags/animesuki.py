"""AnimeSuki Template Tags & Filters"""

from django import template, forms

register = template.Library()


@register.filter
def spacer(value):
    """Adds leading space if value is not empty"""
    return ' ' + value if value is not None and value else ''


@register.filter
def field_css(field, css):
    """Rewrites CSS class attribute for a form field; also adds placeholder attribute"""
    return field.as_widget(attrs={'class': css, 'placeholder': field.label})


@register.filter
def is_checkbox(field):
    """Returns True if field is a checkbox"""
    return isinstance(field.field.widget, forms.CheckboxInput)


@register.filter
def subset(obj, keys):
    """Returns subset of the dictionary object with only the specified keys (as comma separated list)"""
    return [obj[key] for key in keys.split(',')]


@register.filter
def csvlist(value, index):
    """Returns a single value from a comma separated list of values"""
    return str(value).split(',')[index]


@register.simple_tag
def get_absolute_url(obj, name, *args):
    """"Calls get_absolute_url() method on a model object with a name argument"""
    # Note: if you don't need the name argument, just use {{ model.get_absolute_url }} directly
    return obj.get_absolute_url(name, *args)


@register.simple_tag
def build_absolute_uri(request, obj, *args):
    """"Calls build_absolute_uri() method on the request using an object's get_absolute_url method"""
    # Note: if you don't need the object argument, just use {{ request.build_absolute_uri }} directly
    return request.build_absolute_uri(obj.get_absolute_url(*args))
