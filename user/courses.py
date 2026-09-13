from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from db.models import Course, CourseModule, Lesson, Video
from shared.utils import CustomResponse


class Courses(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        print("Fetching active courses")
        courses = Course.objects.filter(
            is_published=True
        ).order_by(
            "sort_order"
        )
        data = []
        for course in courses:
            data.append({
                "id": str(course.id),
                "name": course.title,
                "description": str(course.description),
                "thumbnail": course.thumbnail,
                "level": course.level,
                "total_lessons": course.total_lessons,
                "duration": course.duration,
            })
        return CustomResponse.successResponse(
            data=data,
            description="Courses fetched successfully"
        )


class CourseModuleAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        print("Fetching active modules")
        modules = CourseModule.objects.filter(
            is_published=True
        ).order_by(
            "sort_order"
        )
        data = []
        for module in modules:
            data.append({
                "id": str(module.id),
                "title": module.title,
                "description": str(module.description),
            })
        return CustomResponse.successResponse(
            data=data,
            description="Modules fetched successfully"
        )

class CourseLessonsAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        print("Fetching active lessons")
        lessons = Lesson.objects.filter(
            is_published=True
        ).order_by(
            "sort_order"
        )
        data = []
        for lesson in lessons:
            data.append({
                "id": str(lesson.id),
                "title": lesson.title,
                "description": str(lesson.description),
                "video": f"https://{settings.AWS_CLOUD_FRONT_DOMAIN}/{lesson.video}",
                "thumbnail": str(lesson.thumbnail),
                "duration": lesson.duration,
                "is_preview": lesson.is_preview,
                "is_published": lesson.is_published,
            })
        return CustomResponse.successResponse(
            data=data,
            description="Lessons fetched successfully"
        )




