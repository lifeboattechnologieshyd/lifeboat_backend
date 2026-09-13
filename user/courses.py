from django.conf import settings
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from db.models import Course, CourseModule, Lesson, Video, LessonVideo
from shared.Constants import LANGUAGES
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


class CourseDetails(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, course_id):
        course = (
            Course.objects
            .filter(
                id=course_id,
                is_published=True
            )
            .first()
        )
        if not course:
            return CustomResponse.errorResponse(
                description="Course not found",
                data={},
            )
        # -----------------------------------------
        # Get Modules
        # -----------------------------------------

        modules = (
            CourseModule.objects
            .filter(
                course_id=course.id,
                is_published=True
            )
            .prefetch_related(
                "lessons__lesson_videos__video"
            )
            .order_by(
                "sort_order",
                "created_at"
            )
        )
        module_data = []
        course_language_codes = set()
        for module in modules:
            lesson_data = []
            # -----------------------------------------
            # Get Lessons
            # -----------------------------------------
            lessons = (
                module.lessons
                .filter(
                    is_published=True
                )
                .order_by(
                    "sort_order",
                    "created_at"
                )
            )

            for lesson in lessons:
                available_languages = {}
                # -----------------------------------------
                # Get assigned videos
                # -----------------------------------------
                for lesson_video in lesson.lesson_videos.all():
                    video = lesson_video.video
                    if video.status != "ready":
                        continue
                    language_code = video.language
                    if language_code not in LANGUAGES:
                        continue
                    available_languages[language_code] = {
                        "code": language_code,
                        "name": LANGUAGES[language_code]
                    }
                    course_language_codes.add(
                        language_code
                    )

                lesson_data.append({
                    "id": str(lesson.id),
                    "title": lesson.title,
                    "description": lesson.description,
                    "thumbnail": lesson.thumbnail,
                    "duration": lesson.duration,
                    "sort_order": lesson.sort_order,
                    "is_preview": lesson.is_preview,
                    "languages": list(
                        available_languages.values()
                    )
                })

            module_data.append({
                "id": str(module.id),
                "title": module.title,
                "description": module.description,
                "sort_order": module.sort_order,
                "lessons": lesson_data
            })
        # -----------------------------------------
        # Course Languages
        # -----------------------------------------
        course_languages = [
            {
                "code": code,
                "name": LANGUAGES[code]
            }
            for code in LANGUAGES
            if code in course_language_codes
        ]
        # -----------------------------------------
        # Response
        # -----------------------------------------
        return CustomResponse.successResponse(
            description="Course fetched successfully",
            data={
                "id": str(course.id),
                "title": course.title,
                "description": course.description,
                "thumbnail": course.thumbnail,
                "level": course.level,
                "duration": course.duration,
                "languages": course_languages,
                "modules": module_data
            },
            status_code=200
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


class LessonPlaybackAPIView(APIView):

    permission_classes = [IsAuthenticated]
    def get(self, request, lesson_id):
        language = request.query_params.get("language", "english")
        # -----------------------------------------
        # Validate language
        # -----------------------------------------
        if language not in LANGUAGES:
            return CustomResponse.errorResponse(
                description="Invalid language",
                data={}
            )
        lesson = Lesson.objects.filter(id=lesson_id).select_related("module__course").first()
        if not lesson:
            return CustomResponse.errorResponse(
                description="Lesson not found",
                data={}
            )
        lesson_video = (
            LessonVideo.objects
            .filter(
                lesson_id=lesson.id,
                video__language=language
            )
            .select_related("video")
            .first()
        )
        if not lesson_video:
            return CustomResponse.errorResponse(
                description=f"{LANGUAGES[language]} video is not available for this lesson",
                data={
                    "lesson_id": str(lesson.id),
                    "language": language
                }
            )
        video = lesson_video.video
        if not video.hls_key:
            return CustomResponse.errorResponse(
                description="Video playback is not available",
                data={}
            )
        hls_url = f"https://{settings.AWS_CLOUD_FRONT_DOMAIN}/{video.hls_key}"
        return CustomResponse.errorResponse(
            description="Lesson playback details fetched successfully",
            data={
                "lesson": {
                    "id": str(lesson.id),
                    "title": lesson.title,
                    "description": lesson.description,
                    "thumbnail": lesson.thumbnail,
                    "duration": lesson.duration,
                    "is_preview": lesson.is_preview
                },
                "video": {
                    "id": str(video.id),
                    "name": video.name,
                    "language": video.language,
                    "language_name": LANGUAGES[video.language],
                    "duration": video.duration,
                    "hls_url": hls_url
                }
            }
        )





