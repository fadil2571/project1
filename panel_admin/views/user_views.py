from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, View

from panel_admin.models import User
from panel_admin.permissions import AdminRequiredMixin
from panel_admin.services.notification_service import NotificationService


class UserListView(AdminRequiredMixin, ListView):
	template_name = "dashboard/admin/user-list.html"
	context_object_name = "users"
	paginate_by = 20

	def get_queryset(self):
		queryset = User.objects.annotate(order_count=Count("orders"), total_spent=Sum("orders__total")).order_by(
			"-created_at"
		)

		search = self.request.GET.get("search")
		if search:
			queryset = queryset.filter(
				Q(email__icontains=search)
				| Q(first_name__icontains=search)
				| Q(last_name__icontains=search)
			)

		role = self.request.GET.get("role")
		if role:
			queryset = queryset.filter(role_id=role)

		is_suspended = self.request.GET.get("is_suspended")
		if is_suspended == "true":
			queryset = queryset.filter(is_suspended=True)
		elif is_suspended == "false":
			queryset = queryset.filter(is_suspended=False)

		return queryset

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["page_title"] = "Users"
		context["role_choices"] = User.ROLE_CHOICES
		context["current_role"] = self.request.GET.get("role", "")
		context["search_query"] = self.request.GET.get("search", "")
		return context


class UserSuspendView(AdminRequiredMixin, View):
	def post(self, request, pk, *args, **kwargs):
		user = get_object_or_404(User, pk=pk)

		if user == request.user:
			messages.error(request, "Anda tidak dapat menangguhkan akun sendiri.")
			return redirect("panel_admin:user_list")

		reason = request.POST.get("reason", "")

		user.is_suspended = not user.is_suspended
		user.save()

		if user.is_suspended:
			NotificationService.create_notification(
				user=user,
				title="Akun Ditangguhkan",
				message=f"Akun Anda telah ditangguhkan. Alasan: {reason}",
				notification_type="system",
			)
			messages.success(request, f"Pengguna {user.email} telah ditangguhkan.")
		else:
			NotificationService.create_notification(
				user=user,
				title="Akun Diaktifkan Kembali",
				message="Akun Anda telah diaktifkan kembali.",
				notification_type="system",
			)
			messages.success(request, f"Pengguna {user.email} telah diaktifkan kembali.")

		return redirect("panel_admin:user_list")


class UserRoleUpdateView(AdminRequiredMixin, View):
	def post(self, request, pk, *args, **kwargs):
		user = get_object_or_404(User, pk=pk)
		new_role = request.POST.get("role")

		if new_role in [role[0] for role in User.ROLE_CHOICES]:
			old_role = user.role_id
			user.role_id = new_role
			user.save()
			messages.success(
				request,
				f"Role pengguna {user.email} berhasil diubah dari {old_role} menjadi {new_role}.",
			)
		else:
			messages.error(request, "Role tidak valid.")

		return redirect("panel_admin:user_list")

__all__ = ["UserListView", "UserSuspendView", "UserRoleUpdateView"]
