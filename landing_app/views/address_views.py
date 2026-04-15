from django.views.generic import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from panel_admin.models import Address


def _optional_location_value(post_data, *keys):
    for key in keys:
        if key in post_data:
            return post_data.get(key, "").strip()
    return None


import requests
from landing_app.views.frontend_views import get_emsifa_api_base_url

class AddressView(LoginRequiredMixin, View):
    template_name = 'storefront/auth/address.html'
    login_url = '/auth/login/'
    
    def get(self, request, *args, **kwargs):
        # Fallback data if API fails
        fallback_provinces = [
            {'id': '11', 'name': 'ACEH', 'nama': 'ACEH'}, {'id': '12', 'name': 'SUMATERA UTARA', 'nama': 'SUMATERA UTARA'},
            {'id': '13', 'name': 'SUMATERA BARAT', 'nama': 'SUMATERA BARAT'}, {'id': '14', 'name': 'RIAU', 'nama': 'RIAU'},
            {'id': '15', 'name': 'JAMBI', 'nama': 'JAMBI'}, {'id': '16', 'name': 'SUMATERA SELATAN', 'nama': 'SUMATERA SELATAN'},
            {'id': '17', 'name': 'BENGKULU', 'nama': 'BENGKULU'}, {'id': '18', 'name': 'LAMPUNG', 'nama': 'LAMPUNG'},
            {'id': '19', 'name': 'KEPULAUAN BANGKA BELITUNG', 'nama': 'KEPULAUAN BANGKA BELITUNG'},
            {'id': '21', 'name': 'KEPULAUAN RIAU', 'nama': 'KEPULAUAN RIAU'}, {'id': '31', 'name': 'DKI JAKARTA', 'nama': 'DKI JAKARTA'},
            {'id': '32', 'name': 'JAWA BARAT', 'nama': 'JAWA BARAT'}, {'id': '33', 'name': 'JAWA TENGAH', 'nama': 'JAWA TENGAH'},
            {'id': '34', 'name': 'DI YOGYAKARTA', 'nama': 'DI YOGYAKARTA'}, {'id': '35', 'name': 'JAWA TIMUR', 'nama': 'JAWA TIMUR'},
            {'id': '36', 'name': 'BANTEN', 'nama': 'BANTEN'}, {'id': '51', 'name': 'BALI', 'nama': 'BALI'},
            {'id': '52', 'name': 'NUSA TENGGARA BARAT', 'nama': 'NUSA TENGGARA BARAT'}, {'id': '53', 'name': 'NUSA TENGGARA TIMUR', 'nama': 'NUSA TENGGARA TIMUR'},
            {'id': '61', 'name': 'KALIMANTAN BARAT', 'nama': 'KALIMANTAN BARAT'}, {'id': '62', 'name': 'KALIMANTAN TENGAH', 'nama': 'KALIMANTAN TENGAH'},
            {'id': '63', 'name': 'KALIMANTAN SELATAN', 'nama': 'KALIMANTAN SELATAN'}, {'id': '64', 'name': 'KALIMANTAN TIMUR', 'nama': 'KALIMANTAN TIMUR'},
            {'id': '65', 'name': 'KALIMANTAN UTARA', 'nama': 'KALIMANTAN UTARA'}, {'id': '71', 'name': 'SULAWESI UTARA', 'nama': 'SULAWESI UTARA'},
            {'id': '72', 'name': 'SULAWESI TENGAH', 'nama': 'SULAWESI TENGAH'}, {'id': '73', 'name': 'SULAWESI SELATAN', 'nama': 'SULAWESI SELATAN'},
            {'id': '74', 'name': 'SULAWESI TENGGARA', 'nama': 'SULAWESI TENGGARA'}, {'id': '75', 'name': 'GORONTALO', 'nama': 'GORONTALO'},
            {'id': '76', 'name': 'SULAWESI BARAT', 'nama': 'SULAWESI BARAT'}, {'id': '81', 'name': 'MALUKU', 'nama': 'MALUKU'},
            {'id': '82', 'name': 'MALUKU UTARA', 'nama': 'MALUKU UTARA'}, {'id': '91', 'name': 'PAPUA BARAT', 'nama': 'PAPUA BARAT'},
            {'id': '94', 'name': 'PAPUA', 'nama': 'PAPUA'}
        ]

        addresses = request.user.addresses.all()
        edit_id = request.GET.get('edit')
        edit_address = None
        
        if edit_id:
            edit_address = get_object_or_404(Address, id=edit_id, user=request.user)
        
        # Fetch provinces for the dropdown
        provinces = []
        try:
            url = f"{get_emsifa_api_base_url()}/provinces.json"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                provinces = response.json()
            else:
                provinces = fallback_provinces
        except Exception:
            provinces = fallback_provinces

        context = {
            'addresses': addresses,
            'edit_address': edit_address,
            'provinces': provinces,
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        sub_district = _optional_location_value(request.POST, 'sub_district', 'district')
        village = _optional_location_value(request.POST, 'village')
        
        if action == 'add':
            Address.objects.create(
                user=request.user,
                label=request.POST.get('label', 'Rumah'),
                recipient_name=request.POST.get('recipient_name'),
                recipient_phone=request.POST.get('recipient_phone'),
                address=request.POST.get('address'),
                city=request.POST.get('city'),
                province=request.POST.get('province'),
                sub_district=sub_district or '',
                village=village or '',
                postal_code=request.POST.get('postal_code'),
                is_default=request.POST.get('is_default') == 'on'
            )
            messages.success(request, 'Alamat berhasil ditambahkan.')
        
        elif action == 'edit':
            address_id = request.POST.get('address_id')
            address = get_object_or_404(Address, id=address_id, user=request.user)
            
            address.label = request.POST.get('label', 'Rumah')
            address.recipient_name = request.POST.get('recipient_name')
            address.recipient_phone = request.POST.get('recipient_phone')
            address.address = request.POST.get('address')
            address.city = request.POST.get('city')
            address.province = request.POST.get('province')
            if sub_district is not None:
                address.sub_district = sub_district
            if village is not None:
                address.village = village
            address.postal_code = request.POST.get('postal_code')
            address.is_default = request.POST.get('is_default') == 'on'
            address.save()
            
            messages.success(request, 'Alamat berhasil diperbarui.')
        
        elif action == 'delete':
            address_id = request.POST.get('address_id')
            address = get_object_or_404(Address, id=address_id, user=request.user)
            address.delete()
            messages.success(request, 'Alamat berhasil dihapus.')
        
        elif action == 'set_default':
            address_id = request.POST.get('address_id')
            address = get_object_or_404(Address, id=address_id, user=request.user)
            address.is_default = True
            address.save()
            messages.success(request, 'Alamat utama berhasil diubah.')
        
        return redirect('landing_app:addresses')
