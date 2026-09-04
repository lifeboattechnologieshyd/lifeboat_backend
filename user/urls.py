from django.urls import path

from user.views import SignUpCheck

urlpatterns = [
    path('email', SignUpCheck.as_view())

]