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


class AddressView(LoginRequiredMixin, View):
    template_name = 'storefront/auth/address.html'
    login_url = '/auth/login/'
    
    def get(self, request, *args, **kwargs):
        addresses = request.user.addresses.all()
        edit_id = request.GET.get('edit')
        edit_address = None
        
        if edit_id:
            edit_address = get_object_or_404(Address, id=edit_id, user=request.user)
        
        context = {
            'addresses': addresses,
            'edit_address': edit_address,
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
