from django.urls import path
from backoffice.plans import SubPlans

urlpatterns = [
    path('plans', SubPlans.as_view()),
    path('plans/<uuid:plan_id>', SubPlans.as_view()),
]