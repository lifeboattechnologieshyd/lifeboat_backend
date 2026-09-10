from django.db.models import Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from db.models import Category, Technology, Course
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

class TechnologyListCreate(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        technologies = Technology.objects.prefetch_related("categories").all()

        data = []

        for technology in technologies:

            categories = [
                {
                    "id": str(category.id),
                    "name": category.name
                }
                for category in technology.categories.all()
            ]

            data.append({
                "id": str(technology.id),
                "name": technology.name,
                "slug": technology.slug,
                "description": technology.description,
                "categories": categories,
                "is_active": technology.is_active,
                "sort_order": technology.sort_order,
                "created_at": technology.created_at,
                "updated_at": technology.updated_at,
            })

        return CustomResponse.successResponse(
            data=data,
            description="Technologies fetched successfully"
        )

    def post(self, request):

        name = request.data.get("name")
        description = request.data.get("description")
        category_ids = request.data.get("category_ids", [])
        sort_order = request.data.get("sort_order", 0)

        if not name:
            return CustomResponse.errorResponse(
                description="Technology name is required"
            )

        name = name.strip()

        if Technology.objects.filter(name__iexact=name).exists():
            return CustomResponse.errorResponse(
                description="Technology already exists"
            )

        if not isinstance(category_ids, list):
            return CustomResponse.errorResponse(
                description="category_ids must be a list"
            )

        categories = Category.objects.filter(
            id__in=category_ids,
            is_active=True
        )

        if len(categories) != len(set(category_ids)):
            return CustomResponse.errorResponse(
                description="One or more invalid category IDs"
            )

        technology = Technology.objects.create(
            name=name,
            description=description,
            sort_order=sort_order
        )

        technology.categories.set(categories)

        return CustomResponse.successResponse(
            data={
                "id": str(technology.id),
                "name": technology.name,
                "slug": technology.slug,
                "description": technology.description,
                "categories": [
                    {
                        "id": str(category.id),
                        "name": category.name
                    }
                    for category in technology.categories.all()
                ],
                "is_active": technology.is_active,
                "sort_order": technology.sort_order,
            },
            description="Technology created successfully"
        )

    def put(self, request, technology_id):

        technology = Technology.objects.filter(
            id=technology_id
        ).first()

        if not technology:
            return CustomResponse.errorResponse(
                description="Technology not found"
            )

        name = request.data.get("name")
        description = request.data.get("description")
        category_ids = request.data.get("category_ids")
        sort_order = request.data.get("sort_order")
        is_active = request.data.get("is_active")

        if name is not None:

            name = name.strip()

            if not name:
                return CustomResponse.errorResponse(
                    description="Technology name cannot be empty"
                )

            if Technology.objects.filter(
                    name__iexact=name
            ).exclude(
                id=technology.id
            ).exists():
                return CustomResponse.errorResponse(
                    description="Technology already exists"
                )

            technology.name = name
        if description is not None:
            technology.description = description

        if category_ids is not None:
            if not isinstance(category_ids, list):
                return CustomResponse.errorResponse(
                    description="category_ids must be a list"
                )
            categories = Category.objects.filter(
                id__in=category_ids,
                is_active=True
            )
            if len(categories) != len(set(category_ids)):
                return CustomResponse.errorResponse(
                    description="One or more invalid category IDs"
                )
            technology.categories.set(categories)
        if sort_order is not None:
            technology.sort_order = sort_order
        if is_active is not None:
            technology.is_active = is_active
        technology.save()
        return CustomResponse.successResponse(
            data={
                "id": str(technology.id),
                "name": technology.name,
                "slug": technology.slug,
                "description": technology.description,
                "categories": [
                    {
                        "id": str(category.id),
                        "name": category.name
                    }
                    for category in technology.categories.all()
                ],
                "is_active": technology.is_active,
                "sort_order": technology.sort_order,
            },
            description="Technology updated successfully"
        )

    def delete(self, request, technology_id):

        technology = Technology.objects.filter(
            id=technology_id
        ).first()

        if not technology:
            return CustomResponse.errorResponse(
                description="Technology not found"
            )

        technology.is_active = False

        technology.save(
            update_fields=[
                "is_active",
                "updated_at"
            ]
        )

        return CustomResponse.successResponse(
            data={
                "id": str(technology.id),
                "is_active": technology.is_active
            },
            description="Technology deactivated successfully"
        )

class CourseListCreate(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        courses = Course.objects.prefetch_related(
            "categories",
            "technologies"
        ).all()
        data = []
        for course in courses:
            total_lessons = sum(
                module.lessons.count()
                for module in course.modules.all()
            )
            total_duration = course.modules.filter(
                lessons__is_published=True
            ).aggregate(
                total=Sum("lessons__duration")
            )["total"] or 0
            data.append({
                "id": str(course.id),
                "title": course.title,
                "description": course.description,
                "thumbnail": course.thumbnail,
                "categories": [
                    {
                        "id": str(category.id),
                        "name": category.name
                    }
                    for category in course.categories.all()
                ],
                "technologies": [
                    {
                        "id": str(technology.id),
                        "name": technology.name
                    }
                    for technology in course.technologies.all()
                ],
                "level": course.level,
                "duration": total_duration,
                "total_lessons": total_lessons,
                "is_published": course.is_published,
                "sort_order": course.sort_order,
                "created_at": course.created_at,
                "updated_at": course.updated_at,
            })
        return CustomResponse.successResponse(
            data=data,
            description="Courses fetched successfully"
        )

    def post(self, request):
        title = request.data.get("title")
        description = request.data.get("description")
        thumbnail = request.data.get("thumbnail")
        category_ids = request.data.get("category_ids", [])
        technology_ids = request.data.get("technology_ids", [])
        level = request.data.get("level", "beginner")
        sort_order = request.data.get("sort_order", 0)
        is_published = request.data.get("is_published", False)
        # -------------------------
        # Validation
        # -------------------------
        if not title:
            return CustomResponse.errorResponse(
                description="Course title is required"
            )
        title = title.strip()
        if Course.objects.filter(title__iexact=title).exists():
            return CustomResponse.errorResponse(
                description="Course already exists"
            )
        if not isinstance(category_ids, list):
            return CustomResponse.errorResponse(
                description="category_ids must be a list"
            )
        if not isinstance(technology_ids, list):
            return CustomResponse.errorResponse(
                description="technology_ids must be a list"
            )
        if level not in ["beginner", "intermediate", "advanced"]:
            return CustomResponse.errorResponse(
                description="Invalid course level"
            )
        # -------------------------
        # Categories
        # -------------------------
        categories = Category.objects.filter(
            id__in=category_ids,
            is_active=True
        )
        if len(categories) != len(set(category_ids)):
            return CustomResponse.errorResponse(
                description="One or more invalid category IDs"
            )
        # -------------------------
        # Technologies
        # -------------------------
        technologies = Technology.objects.filter(
            id__in=technology_ids,
            is_active=True
        )
        if len(technologies) != len(set(technology_ids)):
            return CustomResponse.errorResponse(
                description="One or more invalid technology IDs"
            )
        # -------------------------
        # Create
        # -------------------------

        course = Course.objects.create(
            title=title,
            description=description,
            thumbnail=thumbnail,
            level=level,
            sort_order=sort_order,
            is_published=is_published
        )
        course.categories.set(categories)
        course.technologies.set(technologies)
        return CustomResponse.successResponse(
            data={
                "id": str(course.id),
                "title": course.title,
                "description": course.description,
                "thumbnail": course.thumbnail,
                "categories": [
                    {
                        "id": str(category.id),
                        "name": category.name
                    }
                    for category in course.categories.all()
                ],
                "technologies": [
                    {
                        "id": str(technology.id),
                        "name": technology.name
                    }
                    for technology in course.technologies.all()
                ],
                "level": course.level,
                "is_published": course.is_published,
                "sort_order": course.sort_order,
            },
            description="Course created successfully"
        )

    def put(self, request, course_id):
        course = Course.objects.filter(
            id=course_id
        ).first()
        if not course:
            return CustomResponse.errorResponse(
                description="Course not found"
            )

        title = request.data.get("title")
        description = request.data.get("description")
        thumbnail = request.data.get("thumbnail")

        category_ids = request.data.get("category_ids")
        technology_ids = request.data.get("technology_ids")

        level = request.data.get("level")
        sort_order = request.data.get("sort_order")
        is_published = request.data.get("is_published")

        # -------------------------
        # Title
        # -------------------------

        if title is not None:

            title = title.strip()

            if not title:
                return CustomResponse.errorResponse(
                    description="Course title cannot be empty"
                )

            if Course.objects.filter(
                    title__iexact=title
            ).exclude(
                id=course.id
            ).exists():
                return CustomResponse.errorResponse(
                    description="Course already exists"
                )

            course.title = title
        # -------------------------
        # Basic fields
        # -------------------------
        if description is not None:
            course.description = description

        if thumbnail is not None:
            course.thumbnail = thumbnail

        if level is not None:

            if level not in [
                "beginner",
                "intermediate",
                "advanced"
            ]:
                return CustomResponse.errorResponse(
                    description="Invalid course level"
                )

            course.level = level

        if sort_order is not None:
            course.sort_order = sort_order

        if is_published is not None:
            course.is_published = is_published

        # -------------------------
        # Categories
        # -------------------------

        if category_ids is not None:

            if not isinstance(category_ids, list):
                return CustomResponse.errorResponse(
                    description="category_ids must be a list"
                )

            categories = Category.objects.filter(
                id__in=category_ids,
                is_active=True
            )

            if len(categories) != len(set(category_ids)):
                return CustomResponse.errorResponse(
                    description="One or more invalid category IDs"
                )

            course.categories.set(categories)

        # -------------------------
        # Technologies
        # -------------------------

        if technology_ids is not None:

            if not isinstance(technology_ids, list):
                return CustomResponse.errorResponse(
                    description="technology_ids must be a list"
                )

            technologies = Technology.objects.filter(
                id__in=technology_ids,
                is_active=True
            )

            if len(technologies) != len(set(technology_ids)):
                return CustomResponse.errorResponse(
                    description="One or more invalid technology IDs"
                )

            course.technologies.set(technologies)

        course.save()

        return CustomResponse.successResponse(
            data={
                "id": str(course.id),
                "title": course.title,
                "description": course.description,
                "thumbnail": course.thumbnail,

                "categories": [
                    {
                        "id": str(category.id),
                        "name": category.name
                    }
                    for category in course.categories.all()
                ],

                "technologies": [
                    {
                        "id": str(technology.id),
                        "name": technology.name
                    }
                    for technology in course.technologies.all()
                ],

                "level": course.level,
                "is_published": course.is_published,
                "sort_order": course.sort_order,
            },
            description="Course updated successfully"
        )

    def delete(self, request, course_id):

        course = Course.objects.filter(
            id=course_id
        ).first()

        if not course:
            return CustomResponse.errorResponse(
                description="Course not found"
            )

        course.is_published = False

        course.save(
            update_fields=[
                "is_published",
                "updated_at"
            ]
        )

        return CustomResponse.successResponse(
            data={
                "id": str(course.id),
                "is_published": course.is_published
            },
            description="Course unpublished successfully"
        )