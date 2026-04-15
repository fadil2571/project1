"""
RajaOngkir API Service (Komerce)
Handles domestic shipping cost calculation and destination search.

Base URL: https://rajaongkir.komerce.id/api/v1/
Endpoints used:
  - GET  /destination/domestic-destination?search=...
  - POST /calculate/domestic-cost
"""

import os
import requests
import logging

from django.conf import settings
logger = logging.getLogger(__name__)

# Komerce API has different endpoints than the starter API in settings.py
# So we use its own base URL, but share the API key
RAJAONGKIR_KOMERCE_BASE_URL = 'https://rajaongkir.komerce.id/api/v1'
RAJAONGKIR_API_KEY = getattr(settings, 'RAJAONGKIR_API_KEY', '')


class RajaOngkirService:
    """Service to interact with RajaOngkir Komerce API."""

    @staticmethod
    def _headers():
        return {
            'key': RAJAONGKIR_API_KEY,
            'Content-Type': 'application/x-www-form-urlencoded',
        }

    @staticmethod
    def search_destination(keyword, limit=10, offset=0):
        """
        Search domestic destination by keyword (city/district/subdistrict name).
        Returns list of matching destinations with their IDs.
        """
        url = f'{RAJAONGKIR_KOMERCE_BASE_URL}/destination/domestic-destination'
        params = {
            'search': keyword,
            'limit': limit,
            'offset': offset,
        }
        try:
            resp = requests.get(url, params=params, headers={'key': RAJAONGKIR_API_KEY}, timeout=10)
            if resp.status_code == 429:
                return {'success': False, 'error': 'Limit permintaan RajaOngkir tercapai.', 'status': 429}
            resp.raise_for_status()
            data = resp.json()
            return {'success': True, 'data': data}
        except requests.exceptions.Timeout:
            logger.error('RajaOngkir search_destination timeout')
            return {'success': False, 'error': 'Koneksi ke RajaOngkir timeout. Coba lagi.', 'status': 504}
        except requests.exceptions.HTTPError as e:
            st = e.response.status_code if e.response else 502
            return {'success': False, 'error': f'RajaOngkir error: {str(e)}', 'status': st}
        except Exception as e:
            logger.error(f'RajaOngkir search_destination error: {e}')
            return {'success': False, 'error': 'Terjadi kesalahan.', 'status': 500}

    @staticmethod
    def calculate_cost(origin, destination, weight, courier):
        """
        Calculate domestic shipping cost.

        Args:
            origin (str/int): Origin location ID from search_destination
            destination (str/int): Destination location ID from search_destination
            weight (int): Weight in grams
            courier (str): Courier code (e.g. jne, jnt, sicepat, pos, tiki, anteraja)
        
        Returns:
            dict with 'success' and 'data' or 'error' keys
        """
        url = f'{RAJAONGKIR_KOMERCE_BASE_URL}/calculate/domestic-cost'
        payload = {
            'origin': str(origin),
            'destination': str(destination),
            'weight': int(weight),
            'courier': courier.lower(),
        }
        try:
            resp = requests.post(url, data=payload, headers=RajaOngkirService._headers(), timeout=15)
            resp.raise_for_status()
            data = resp.json()
            return {'success': True, 'data': data}
        except requests.exceptions.Timeout:
            logger.error('RajaOngkir calculate_cost timeout')
            return {'success': False, 'error': 'Koneksi ke RajaOngkir timeout. Coba lagi.'}
        except requests.exceptions.RequestException as e:
            logger.error(f'RajaOngkir calculate_cost error: {e}')
            return {'success': False, 'error': f'Gagal menghubungi RajaOngkir: {str(e)}'}
        except Exception as e:
            logger.error(f'RajaOngkir calculate_cost unexpected error: {e}')
            return {'success': False, 'error': 'Terjadi kesalahan.'}
