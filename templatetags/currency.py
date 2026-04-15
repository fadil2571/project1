from django import template

register = template.Library()


@register.filter(name='rupiah')
def rupiah(value):
    """Format angka ke gaya Rupiah Indonesia dengan pemisah ribuan titik."""
    try:
        amount = int(value)
    except (TypeError, ValueError):
        return value
    return f"{amount:,}".replace(',', '.')
