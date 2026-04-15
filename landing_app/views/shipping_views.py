"""
Shipping API Views
Provides AJAX endpoints for RajaOngkir integration:
  - /api/shipping/search-destination/  (GET)
  - /api/shipping/calculate-cost/      (POST)
"""

import json

from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from panel_admin.services.rajaongkir_service import RajaOngkirService


class SearchDestinationView(LoginRequiredMixin, View):
    """Search domestic destinations for origin/destination autocomplete."""

    def get(self, request, *args, **kwargs):
        keyword = request.GET.get('search', '').strip()
        if not keyword or len(keyword) < 2:
            return JsonResponse({'success': False, 'error': 'Masukkan minimal 2 karakter.'}, status=400)

        result = RajaOngkirService.search_destination(keyword, limit=15)
        if result['success']:
            return JsonResponse(result)
        return JsonResponse(result, status=result.get('status', 502))


class CalculateCostView(LoginRequiredMixin, View):
    """Calculate domestic shipping cost via RajaOngkir."""

    def post(self, request, *args, **kwargs):
        # Accept both form-encoded and JSON body
        if request.content_type and 'json' in request.content_type:
            try:
                body = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'error': 'Invalid JSON.'}, status=400)
        else:
            body = request.POST

        origin = body.get('origin', '').strip() if isinstance(body.get('origin'), str) else body.get('origin')
        destination = body.get('destination', '').strip() if isinstance(body.get('destination'), str) else body.get('destination')
        weight = body.get('weight', 0)
        courier = body.get('courier', '').strip() if isinstance(body.get('courier'), str) else body.get('courier', '')

        # Validation
        errors = []
        if not origin:
            errors.append('Origin wajib diisi.')
        if not destination:
            errors.append('Destination wajib diisi.')
        try:
            weight = int(weight)
            if weight <= 0:
                errors.append('Berat harus lebih dari 0 gram.')
        except (ValueError, TypeError):
            errors.append('Berat harus berupa angka.')
        if not courier:
            errors.append('Kurir wajib dipilih.')

        if errors:
            return JsonResponse({'success': False, 'error': ' '.join(errors)}, status=400)

        result = RajaOngkirService.calculate_cost(origin, destination, weight, courier)
        if result['success']:
            return JsonResponse(result)
        return JsonResponse(result, status=502)
