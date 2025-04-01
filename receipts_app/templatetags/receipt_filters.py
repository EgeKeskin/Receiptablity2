from django import template

register = template.Library()

@register.filter
def humanize_room_type(value):
    """Convert 'probabalistic_roulette' => 'Probabalistic Roulette'"""
    if not isinstance(value, str):
        return value
    return ' '.join(word.capitalize() for word in value.split('_'))