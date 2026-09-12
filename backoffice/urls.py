from django.urls import path

from backoffice.courses import CategoryListCreate, TechnologyListCreate, CourseListCreate, CourseModuleListCreate, \
    LessonListCreate, AssignLesson
from backoffice.plans import SubPlans
from backoffice.video_upload import VideoUploadURLAPIView, VideoConvertAPIView, VideoStatusAPIView, Videos

urlpatterns = [
    path('plans', SubPlans.as_view()),
    path('plans/<uuid:plan_id>', SubPlans.as_view()),

    path('category', CategoryListCreate.as_view()),
    path('category/<uuid:category_id>', CategoryListCreate.as_view()),

    path("technologies",TechnologyListCreate.as_view()),
    path("technologies/<uuid:technology_id>",TechnologyListCreate.as_view()),

    path("courses",CourseListCreate.as_view()),
    path("courses/<uuid:course_id>",CourseListCreate.as_view()),

    path("modules",CourseModuleListCreate.as_view()),
    path("modules/<uuid:module_id>",CourseModuleListCreate.as_view()),

    path("lessons", LessonListCreate.as_view()),
    path("lessons/<uuid:lesson_id>",LessonListCreate.as_view()),

    path("videos/upload-url",VideoUploadURLAPIView.as_view()),
    path("videos",Videos.as_view()), #todo : pagination and filter to be added.
    path("videos/convert",VideoConvertAPIView.as_view()),
    path("videos/convert/status",VideoStatusAPIView.as_view()),

    path("assign/video", AssignLesson.as_view()),

]