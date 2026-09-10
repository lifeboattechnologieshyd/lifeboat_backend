from django.urls import path

from backoffice.courses import CategoryListCreate, TechnologyListCreate, CourseListCreate
from backoffice.plans import SubPlans

urlpatterns = [
    path('plans', SubPlans.as_view()),
    path('plans/<uuid:plan_id>', SubPlans.as_view()),

    path('category', CategoryListCreate.as_view()),
    path('category/<uuid:category_id>', CategoryListCreate.as_view()),

    path("technologies",TechnologyListCreate.as_view()),
    path("technologies/<uuid:technology_id>",TechnologyListCreate.as_view()),

    path("courses",CourseListCreate.as_view()),
    path("courses/<uuid:course_id>",CourseListCreate.as_view()),


]