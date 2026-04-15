from panel_admin.models import Category


class CategoryService:
    """Business rules and CRUD operations for categories."""

    @staticmethod
    def list_categories(search_query=None):
        queryset = Category.objects.order_by("created_at")
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
        return queryset

    @staticmethod
    def create_category(data):
        payload = dict(data)
        payload["slug"] = Category.generate_unique_slug(payload["name"])
        return Category.objects.create(**payload)

    @staticmethod
    def update_category(category, data):
        payload = dict(data)
        if "name" in payload and payload["name"] != category.name:
            payload["slug"] = Category.generate_unique_slug(payload["name"], exclude_id=category.id)

        for key, value in payload.items():
            setattr(category, key, value)
        category.save()
        return category

    @staticmethod
    def delete_category(category):
        category.delete()
        return True

    @staticmethod
    def generate_unique_slug(name, exclude_id=None):
        return Category.generate_unique_slug(name, exclude_id=exclude_id)
