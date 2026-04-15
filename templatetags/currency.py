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


@register.filter(name='numberformat')
def numberformat(value):
    """Format angka dengan pemisah ribuan titik (alias untuk rupiah tanpa 'Rp')."""
    try:
        amount = int(value)
    except (TypeError, ValueError):
        return value
    return f"{amount:,}".replace(',', '.')
