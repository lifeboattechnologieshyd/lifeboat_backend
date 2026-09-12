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
                "video": str(lesson.video),
                "thumbnail": str(lesson.thumbnail),
                "duration": lesson.duration,
                "is_preview": lesson.is_preview,
                "is_published": lesson.is_published,
            })
        return CustomResponse.successResponse(
            data=data,
            description="Lessons fetched successfully"
        )

class AssignLesson(APIView):

    def post(self, request):
        data = request.data
        lesson_id = request.data.get("lesson_id")
        video_id = request.data.get("video_id")
        if not lesson_id:
            return CustomResponse.errorResponse(
                description="Lesson ID is required"
            )
        try:
            video = Video.objects.get(id=video_id)
        except Video.DoesNotExist:
            return CustomResponse.errorResponse(
                description="Video not found"
            )
        try:
            lesson = Lesson.objects.get(id=lesson_id)
        except Lesson.DoesNotExist:
            return CustomResponse.errorResponse(
                description="Lesson not found"
            )
            # Video must be successfully converted
        if video.status != "ready":
            return CustomResponse.errorResponse(
                  description="Only ready videos can be assigned to a lesson"
            )

        if not video.hls_key:
            return CustomResponse.errorResponse(
                  description="HLS video is not available"
            )
        # Optional safety check:
        # video and lesson should belong to the same course
        if str(video.course_id) != str(lesson.module.course_id):
            return CustomResponse.errorResponse(
                description="Video and lesson belong to different courses"
            )
        lesson.video = video.hls_key
        lesson.save(
            update_fields=[
                "video_key",
            ]
        )
        video.status = "assigned"
        video.save(
            update_fields=[
                "status",
            ]
        )
        return CustomResponse.successResponse(
            data={
                "video_id": str(video.id),
                "lesson_id": str(lesson.id),
                "video_status": video.status,
                "video_key": video.hls_key
            }
        )



