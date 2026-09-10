from django.urls import path

from user.views import SignUpCheck, ValidateMagicToken, Plans, CreatePayment, Webhook, VerifySubscriptionPaymentAPIView, \
    VerifyOTP, SetPassword, Login, MySubscription, ProfileView

urlpatterns = [
    path('email', SignUpCheck.as_view()),
    path('verify-token', ValidateMagicToken.as_view()),
    path('verify-otp', VerifyOTP.as_view()),
    path('set-password', SetPassword.as_view()),
    path('login', Login.as_view()),
    path('subscription', MySubscription.as_view()),
    path('profile', ProfileView.as_view()),
    path('plans', Plans.as_view()),
    path('create-payment', CreatePayment.as_view()),
    path('webhook', Webhook.as_view()),
    path('verify-payment', VerifySubscriptionPaymentAPIView.as_view())
]