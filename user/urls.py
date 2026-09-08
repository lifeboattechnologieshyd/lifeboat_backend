from django.urls import path

from user.views import SignUpCheck, ValidateMagicToken, Plans

urlpatterns = [
    path('email', SignUpCheck.as_view()),
    path('verify-token', ValidateMagicToken.as_view()),


    path('plans', Plans.as_view())

]