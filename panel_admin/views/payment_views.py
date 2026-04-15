import json

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from panel_admin.models import Payment
from panel_admin.permissions import AdminRequiredMixin
from panel_admin.services.payment_service import PaymentService


class PaymentConfirmView(AdminRequiredMixin, View):
	def post(self, request, *args, **kwargs):
		payment_id = request.POST.get("payment_id")
		action = request.POST.get("action")

		payment = get_object_or_404(Payment, id=payment_id)

		if action == "confirm":
			PaymentService.confirm_payment(payment)
			messages.success(request, "Pembayaran berhasil dikonfirmasi.")
		elif action == "reject":
			reason = request.POST.get("reason", "")
			PaymentService.reject_payment(payment, reason)
			messages.success(request, "Pembayaran berhasil ditolak.")

		return redirect("panel_admin:order_detail", order_number=payment.order.order_number)


@method_decorator(csrf_exempt, name="dispatch")
class PaymentCallbackView(View):
	def post(self, request, *args, **kwargs):
		try:
			data = json.loads(request.body)

			order_id = data.get("order_id")
			transaction_status = data.get("transaction_status")
			transaction_id = data.get("transaction_id")

			PaymentService.handle_callback(order_id, transaction_status, transaction_id)

			return JsonResponse({"status": "success"})
		except Exception as e:
			return JsonResponse({"status": "error", "message": str(e)}, status=400)

__all__ = ["PaymentConfirmView", "PaymentCallbackView"]
