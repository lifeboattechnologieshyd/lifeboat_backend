from django.urls import path

from backoffice.courses import CategoryListCreate
from backoffice.plans import SubPlans

urlpatterns = [
    path('plans', SubPlans.as_view()),
    path('plans/<uuid:plan_id>', SubPlans.as_view()),

    path('category', CategoryListCreate.as_view()),
    path('category/<uuid:category_id>', CategoryListCreate.as_view()),
]