from django.db.models import Sum
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from db.models import Category, Technology, Course, CourseModule, Lesson, Video, LessonVideo
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


class CourseModuleListCreate(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        modules = CourseModule.objects.select_related(
            "course"
        ).all()
        data = []
        for module in modules:

            data.append({
                "id": str(module.id),
                "course": {
                    "id": str(module.course.id),
                    "title": module.course.title
                },
                "title": module.title,
                "description": module.description,
                "sort_order": module.sort_order,
                "is_published": module.is_published,
                "created_at": module.created_at,
                "updated_at": module.updated_at,
            })

        return CustomResponse.successResponse(
            data=data,
            description="Course modules fetched successfully"
        )

    def post(self, request):

        course_id = request.data.get("course_id")
        title = request.data.get("title")
        description = request.data.get("description")
        sort_order = request.data.get("sort_order", 0)
        is_published = request.data.get("is_published", False)

        # -------------------------
        # Validation
        # -------------------------

        if not course_id:
            return CustomResponse.errorResponse(
                description="Course ID is required"
            )

        if not title:
            return CustomResponse.errorResponse(
                description="Module title is required"
            )

        title = title.strip()

        if not title:
            return CustomResponse.errorResponse(
                description="Module title cannot be empty"
            )

        course = Course.objects.filter(
            id=course_id
        ).first()

        if not course:
            return CustomResponse.errorResponse(
                description="Course not found"
            )

        # -------------------------
        # Create
        # -------------------------

        module = CourseModule.objects.create(
            course=course,
            title=title,
            description=description,
            sort_order=sort_order,
            is_published=is_published
        )

        return CustomResponse.successResponse(
            data={
                "id": str(module.id),
                "course": {
                    "id": str(course.id),
                    "title": course.title
                },
                "title": module.title,
                "description": module.description,
                "sort_order": module.sort_order,
                "is_published": module.is_published,
            },
            description="Course module created successfully"
        )

    def put(self, request, module_id):

        module = CourseModule.objects.filter(
            id=module_id
        ).first()

        if not module:
            return CustomResponse.errorResponse(
                description="Course module not found"
            )

        course_id = request.data.get("course_id")
        title = request.data.get("title")
        description = request.data.get("description")
        sort_order = request.data.get("sort_order")
        is_published = request.data.get("is_published")

        # -------------------------
        # Course
        # -------------------------

        if course_id is not None:

            course = Course.objects.filter(
                id=course_id
            ).first()

            if not course:
                return CustomResponse.errorResponse(
                    description="Course not found"
                )

            module.course = course

        # -------------------------
        # Title
        # -------------------------

        if title is not None:

            title = title.strip()

            if not title:
                return CustomResponse.errorResponse(
                    description="Module title cannot be empty"
                )

            module.title = title

        # -------------------------
        # Other fields
        # -------------------------

        if description is not None:
            module.description = description

        if sort_order is not None:
            module.sort_order = sort_order

        if is_published is not None:
            module.is_published = is_published

        module.save()

        return CustomResponse.successResponse(
            data={
                "id": str(module.id),
                "course": {
                    "id": str(module.course.id),
                    "title": module.course.title
                },
                "title": module.title,
                "description": module.description,
                "sort_order": module.sort_order,
                "is_published": module.is_published,
            },
            description="Course module updated successfully"
        )

    def delete(self, request, module_id):

        module = CourseModule.objects.filter(
            id=module_id
        ).first()

        if not module:
            return CustomResponse.errorResponse(
                description="Course module not found"
            )

        module.is_published = False

        module.save(
            update_fields=[
                "is_published",
                "updated_at"
            ]
        )

        return CustomResponse.successResponse(
            data={
                "id": str(module.id),
                "is_published": module.is_published
            },
            description="Course module unpublished successfully"
        )


class LessonListCreate(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        lessons = Lesson.objects.select_related(
            "module",
            "module__course"
        ).all()
        data = []
        for lesson in lessons:
            data.append({
                "id": str(lesson.id),
                "course": {
                    "id": str(lesson.module.course.id),
                    "title": lesson.module.course.title
                },
                "module": {
                    "id": str(lesson.module.id),
                    "title": lesson.module.title
                },
                "title": lesson.title,
                "description": lesson.description,
                "thumbnail": lesson.thumbnail,
                "duration": lesson.duration,
                "sort_order": lesson.sort_order,
                "is_preview": lesson.is_preview,
                "is_published": lesson.is_published,
                "created_at": lesson.created_at,
                "updated_at": lesson.updated_at,
            })

        return CustomResponse.successResponse(
            data=data,
            description="Lessons fetched successfully"
        )

    def post(self, request):

        module_id = request.data.get("module_id")
        title = request.data.get("title")
        description = request.data.get("description")
        video_key = request.data.get("video_key")
        thumbnail = request.data.get("thumbnail")
        duration = request.data.get("duration", 0)
        sort_order = request.data.get("sort_order", 0)
        is_preview = request.data.get("is_preview", False)
        is_published = request.data.get("is_published", False)

        # -------------------------
        # Validation
        # -------------------------

        if not module_id:
            return CustomResponse.errorResponse(
                description="Module ID is required"
            )

        if not title:
            return CustomResponse.errorResponse(
                description="Lesson title is required"
            )

        title = title.strip()

        if not title:
            return CustomResponse.errorResponse(
                description="Lesson title cannot be empty"
            )

        module = CourseModule.objects.select_related(
            "course"
        ).filter(
            id=module_id
        ).first()

        if not module:
            return CustomResponse.errorResponse(
                description="Course module not found"
            )

        # -------------------------
        # Create
        # -------------------------

        lesson = Lesson.objects.create(
            module=module,
            title=title,
            description=description,
            thumbnail=thumbnail,
            duration=duration,
            sort_order=sort_order,
            is_preview=is_preview,
            is_published=is_published
        )

        return CustomResponse.successResponse(
            data={
                "id": str(lesson.id),

                "course": {
                    "id": str(module.course.id),
                    "title": module.course.title
                },

                "module": {
                    "id": str(module.id),
                    "title": module.title
                },

                "title": lesson.title,
                "description": lesson.description,
                "thumbnail": lesson.thumbnail,
                "duration": lesson.duration,
                "sort_order": lesson.sort_order,
                "is_preview": lesson.is_preview,
                "is_published": lesson.is_published,
            },
            description="Lesson created successfully"
        )

    def put(self, request, lesson_id):

        lesson = Lesson.objects.filter(
            id=lesson_id
        ).first()

        if not lesson:
            return CustomResponse.errorResponse(
                description="Lesson not found"
            )

        module_id = request.data.get("module_id")
        title = request.data.get("title")
        description = request.data.get("description")
        video_key = request.data.get("video_key")
        thumbnail = request.data.get("thumbnail")
        duration = request.data.get("duration")
        sort_order = request.data.get("sort_order")
        is_preview = request.data.get("is_preview")
        is_published = request.data.get("is_published")

        # -------------------------
        # Module
        # -------------------------

        if module_id is not None:

            module = CourseModule.objects.filter(
                id=module_id
            ).first()

            if not module:
                return CustomResponse.errorResponse(
                    description="Course module not found"
                )

            lesson.module = module

        # -------------------------
        # Title
        # -------------------------

        if title is not None:

            title = title.strip()

            if not title:
                return CustomResponse.errorResponse(
                    description="Lesson title cannot be empty"
                )

            lesson.title = title

        # -------------------------
        # Other fields
        # -------------------------

        if description is not None:
            lesson.description = description

        # if video_key is not None:
        #     lesson.video_key = video_key

        if thumbnail is not None:
            lesson.thumbnail = thumbnail

        if duration is not None:
            lesson.duration = duration

        if sort_order is not None:
            lesson.sort_order = sort_order

        if is_preview is not None:
            lesson.is_preview = is_preview

        if is_published is not None:
            lesson.is_published = is_published
        lesson.save()
        return CustomResponse.successResponse(
            data={
                "id": str(lesson.id),
                "course": {
                    "id": str(lesson.module.course.id),
                    "title": lesson.module.course.title
                },
                "module": {
                    "id": str(lesson.module.id),
                    "title": lesson.module.title
                },
                "title": lesson.title,
                "description": lesson.description,
                "video_key": lesson.video_key,
                "thumbnail": lesson.thumbnail,
                "duration": lesson.duration,
                "sort_order": lesson.sort_order,
                "is_preview": lesson.is_preview,
                "is_published": lesson.is_published,
            },
            description="Lesson updated successfully"
        )

    def delete(self, request, lesson_id):
        lesson = Lesson.objects.filter(
            id=lesson_id
        ).first()
        if not lesson:
            return CustomResponse.errorResponse(
                description="Lesson not found"
            )
        lesson.is_published = False
        lesson.save(
            update_fields=[
                "is_published",
                "updated_at"
            ]
        )
        return CustomResponse.successResponse(
            data={
                "id": str(lesson.id),
                "is_published": lesson.is_published
            },
            description="Lesson unpublished successfully"
        )



# class AssignLesson(APIView):
#
#     def post(self, request):
#         lesson_id = request.data.get("lesson_id")
#         video_id = request.data.get("video_id")
#         if not lesson_id:
#             return CustomResponse.errorResponse(
#                 description="Lesson ID is required"
#             )
#         try:
#             video = Video.objects.get(id=video_id)
#         except Video.DoesNotExist:
#             return CustomResponse.errorResponse(
#                 description="Video not found"
#             )
#         try:
#             lesson = Lesson.objects.get(id=lesson_id)
#         except Lesson.DoesNotExist:
#             return CustomResponse.errorResponse(
#                 description="Lesson not found"
#             )
#             # Video must be successfully converted
#         if video.status != "ready":
#             return CustomResponse.errorResponse(
#                   description="Only ready videos can be assigned to a lesson"
#             )
#
#         if not video.hls_key:
#             return CustomResponse.errorResponse(
#                   description="HLS video is not available"
#             )
#         # Optional safety check:
#         # video and lesson should belong to the same course
#         if str(video.course_id) != str(lesson.module.course_id):
#             return CustomResponse.errorResponse(
#                 description="Video and lesson belong to different courses"
#             )
#         lesson.video = video.hls_key
#         lesson.save(
#             update_fields=[
#                 "video",
#             ]
#         )
#         video.status = "assigned"
#         video.save(
#             update_fields=[
#                 "status",
#             ]
#         )
#         return CustomResponse.successResponse(
#             data={
#                 "video_id": str(video.id),
#                 "lesson_id": str(lesson.id),
#                 "video_status": video.status,
#                 "video_key": video.hls_key
#             }
#         )

class LessonVideosAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, lesson_id):

        lesson = Lesson.objects.filter(id=lesson_id).first()
        if not lesson:
            return CustomResponse.errorResponse(
                description="lesson not found",
                data={},
            )
        lesson_videos = (
            LessonVideo.objects
            .filter(lesson=lesson)
            .select_related("video")
            .order_by("video__language")
        )

        data = []
        for item in lesson_videos:
            video = item.video
            data.append({
                "lesson_video_id": str(item.id),
                "video_id": str(video.id),
                "name": video.name,
                "language": video.language,
                "language_name": video.get_language_display(),
                "status": video.status,
                "duration": video.duration,
                "file_size": video.file_size,
                "original_key": video.original_key,
                "hls_key": video.hls_key,
                "media_job_id": video.media_job_id,
                "error_message": video.error_message,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
            })
        return CustomResponse.successResponse(
            description="Lesson videos fetched successfully",
            data=data
        )

    def delete(self, request, lesson_video_id):

        lesson_video = get_object_or_404(
            LessonVideo.objects.select_related("video"),
            id=lesson_video_id
        )
        video = lesson_video.video
        # Remove the lesson-video relationship
        lesson_video.delete()
        # If this video is not assigned to any other lesson,
        # mark it as ready again.
        if not LessonVideo.objects.filter(
                video=video
        ).exists():
            video.status = "ready"
            video.save(
                update_fields=[
                    "status",
                    "updated_at"
                ]
            )
        return CustomResponse.successResponse(
            description="Video removed from lesson successfully",
            data={
                "video_id": str(video.id),
                "language": video.language,
                "language_name": video.get_language_display(),
                "video_status": video.status
            }
        )