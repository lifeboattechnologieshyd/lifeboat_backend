from django.urls import path

from backoffice.plans import SubPlans

urlpatterns = [
    path('plans', SubPlans.as_view()),
]