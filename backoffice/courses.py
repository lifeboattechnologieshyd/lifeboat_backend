from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from db.models import Category
from shared.utils import CustomResponse


class CategoryListCreate(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        categories = Category.objects.all()
        data = []
        for category in categories:
            data.append({
                "id": str(category.id),
                "name": category.name,
                "slug": category.slug,
                "description": category.description,
                "is_active": category.is_active,
                "sort_order": category.sort_order,
                "created_at": category.created_at,
                "updated_at": category.updated_at,
            })
        return CustomResponse.successResponse(
            data=data,
            description="Categories fetched successfully"
        )

    def post(self, request):

        name = request.data.get("name")
        description = request.data.get("description")
        icon = request.data.get("icon")
        sort_order = request.data.get("sort_order", 0)

        if not name:
            return CustomResponse.errorResponse(
                description="Category name is required"
            )

        name = name.strip()

        if Category.objects.filter(name__iexact=name).exists():
            return CustomResponse.errorResponse(
                description="Category already exists"
            )

        category = Category.objects.create(
            name=name,
            icon=icon,
            description=description,
            sort_order=sort_order
        )

        return CustomResponse.successResponse(
            data={
                "id": str(category.id),
                "name": category.name,
                "slug": category.slug,
                "description": category.description,
                "is_active": category.is_active,
                "sort_order": category.sort_order,
            },
            description="Category created successfully"
        )

    def put(self, request, category_id):
        category = Category.objects.filter(
            id=category_id
        ).first()

        if not category:
            return CustomResponse.errorResponse(
                description="Category not found"
            )
        name = request.data.get("name")
        icon = request.data.get("icon")
        description = request.data.get("description")
        sort_order = request.data.get("sort_order")
        is_active = request.data.get("is_active")
        if name is not None:
            name = name.strip()
            if not name:
                return CustomResponse.errorResponse(
                    description="Category name cannot be empty"
                )
            if Category.objects.filter(
                    name__iexact=name
            ).exclude(
                id=category.id
            ).exists():
                return CustomResponse.errorResponse(
                    description="Category already exists"
                )
            category.name = name
        if description is not None:
            category.description = description
        if sort_order is not None:
            category.sort_order = sort_order
        if is_active is not None:
            category.is_active = is_active
        if icon is not None:
            category.icon = icon
        category.save()
        return CustomResponse.successResponse(
            data={
                "id": str(category.id),
                "name": category.name,
                "slug": category.slug,
                "description": category.description,
                "is_active": category.is_active,
                "sort_order": category.sort_order,
            },
            description="Category updated successfully"
        )

    def delete(self, request, category_id):
        category = Category.objects.filter(
            id=category_id
        ).first()
        if not category:
            return CustomResponse.errorResponse(
                description="Category not found"
            )
        category.is_active = False
        category.save(update_fields=["is_active", "updated_at"])
        return CustomResponse.successResponse(
            data={
                "id": str(category.id),
                "is_active": category.is_active
            },
            description="Category deactivated successfully"
        )
