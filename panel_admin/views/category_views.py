from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from panel_admin.models import Category
from panel_admin.permissions import AdminRequiredMixin
from panel_admin.services.category_service import CategoryService


class CategoryListView(AdminRequiredMixin, ListView):
    template_name = "dashboard/admin/category-list.html"
    model = Category
    context_object_name = "categories"
    paginate_by = 20

    def get_queryset(self):
        return CategoryService.list_categories(self.request.GET.get("q", "").strip())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Categories"
        context["search_query"] = self.request.GET.get("q", "").strip()
        context["icon_options"] = Category.ICON_CHOICES
        return context


class CategoryCreateView(AdminRequiredMixin, CreateView):
    model = Category
    template_name = "dashboard/admin/category-create.html"
    fields = ["name", "icon_key", "is_active"]

    def get_success_url(self):
        messages.success(self.request, "Kategori berhasil ditambahkan.")
        return reverse_lazy("panel_admin:category_list")

    def form_valid(self, form):
        try:
            data = form.cleaned_data
            self.object = CategoryService.create_category(data)
            return HttpResponseRedirect(self.get_success_url())
        except ValidationError as e:
            form.add_error("name", e.message)
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Categories"
        context["action"] = "create"
        context["icon_options"] = Category.ICON_CHOICES
        return context


class CategoryUpdateView(AdminRequiredMixin, UpdateView):
    model = Category
    template_name = "dashboard/admin/category-edit.html"
    fields = ["name", "icon_key", "is_active"]

    def get_success_url(self):
        messages.success(self.request, "Kategori berhasil diperbarui.")
        return reverse_lazy("panel_admin:category_list")

    def form_valid(self, form):
        try:
            data = form.cleaned_data
            self.object = CategoryService.update_category(self.get_object(), data)
            return HttpResponseRedirect(self.get_success_url())
        except ValidationError as e:
            form.add_error("name", e.message)
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Categories"
        context["action"] = "edit"
        context["icon_options"] = Category.ICON_CHOICES
        return context


class CategoryDeleteView(AdminRequiredMixin, DeleteView):
    model = Category
    template_name = "dashboard/admin/category-detail.html"

    def get_success_url(self):
        messages.success(self.request, "Kategori berhasil dihapus.")
        return reverse_lazy("panel_admin:category_list")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        CategoryService.delete_category(self.object)
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Categories"
        return context
