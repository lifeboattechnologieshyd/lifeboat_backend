from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from db.models import Course
from shared.utils import CustomResponse


class Courses(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        print("Fetching active plans")
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
