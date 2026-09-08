import hashlib

from django.utils import timezone
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from db.models import UserMaster, MagicLoginToken, Plan, Subscription
from shared.utils import CustomResponse, send_magic_login_link
from user.razorpay_helper import create_razorpay_subscription


class SignUpCheck(APIView):

    def post(self, request):
        print("checking if email exists or not in signup flow.")
        data = request.data
        email = data.get("email")
        device_id = data.get("device_id")
        fcm_id = data.get("fcm_id")
        os = data.get("os")
        model = data.get("model")
        os_version = data.get("os_version")
        user = UserMaster.objects.filter(email=email).first()
        if user:
            print("User exists so asking him password")
            return CustomResponse.successResponse(data={
                "is_login_flow":True,
                "email": user.email
            }, description="Please enter password")
        else:
            print("user does not exists so sending an email")
            send_magic_login_link(email)
            return CustomResponse.successResponse(data={
                "is_login_flow":False,
            }, description="Mail sent successfully")

class ValidateMagicToken(APIView):

    def post(self, request):
        token = request.data.get('token', "")
        if token:
            # Hash the token received from URL
            token_hash = hashlib.sha256(
                token.encode()
            ).hexdigest()
            # Find valid token
            magic_token = MagicLoginToken.objects.filter(
                token_hash=token_hash,
                used_at__isnull=True
            ).first()

            if not magic_token:
                return CustomResponse.errorResponse(
                    description="Invalid or already used login link"
                )
            # Check expiry
            if magic_token.expires_at <= timezone.now():
                return CustomResponse.errorResponse(
                    description="This login link has expired"
                )
            email = magic_token.email
            print(f"Magic link validated for {email}")
            # Check if user already exists
            user = UserMaster.objects.filter(
                email=email
            ).first()
            # Create user only after successful magic-link validation
            if not user:
                user = UserMaster.objects.create(
                    email=email,
                    username=email.split("@")[0]
                )
                print(f"New user created: {user.id}")
            # Mark token as used
            magic_token.used_at = timezone.now()
            magic_token.save(
                update_fields=["used_at"]
            )
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            return CustomResponse.successResponse(
                data={
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "email": user.email,
                    "is_new_user": True
                },
                description="Email verified successfully"
            )
        else:
            return CustomResponse.errorResponse(data={},
                                                description="Link Expired or Invalid, Please try again")

class Plans(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        print("Fetching active plans")
        plans = Plan.objects.filter(
            is_active=True
        ).order_by(
            "price"
        )
        data = []
        for plan in plans:
            data.append({
                "id": str(plan.id),
                "name": plan.name,
                "code": plan.code,
                "price": str(plan.price),
                "billing_interval": plan.billing_interval,
                "billing_interval_count": plan.billing_interval_count,
                "description": plan.description,
                "is_recommended": plan.is_recommended
            })
        return CustomResponse.successResponse(
            data=data,
            description="Plans fetched successfully"
        )



class CreatePayment(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        plan_id = request.data.get("plan_id")
        if not plan_id:
            return CustomResponse().errorResponse(
                data={},
                description="Plan is required."
            )
        plan = Plan.objects.filter(
            id=plan_id,
            is_active=True,
        )
        if not plan:
            return CustomResponse().errorResponse(
                data={},
                description="Invalid Plan Selected"
            )
        if not plan.razorpay_plan_id:
            return CustomResponse.errorResponse(
                description="Razorpay plan is not configured"
            )
        # Check if user already has an active subscription
        active_subscription = Subscription.objects.filter(
            user=user,
            status="active"
        ).first()
        #todo: need to check if upgrade is possible.
        if active_subscription:
            return CustomResponse.errorResponse(
                description="You already have an active subscription"
            )
        print("========== CREATING RAZORPAY SUBSCRIPTION ==========")
        razorpay_response = create_razorpay_subscription(
            plan_id=plan.razorpay_plan_id,
        )
        print("========== RAZORPAY RESPONSE ==========")
        print(razorpay_response)
        razorpay_subscription_id = razorpay_response["id"]
        # Save Lifeboat subscription
        subscription = Subscription.objects.create(
            user=user,
            plan=plan,
            razorpay_subscription_id=razorpay_subscription_id,
            status="created"
        )
        return CustomResponse.successResponse(
            data={
                "subscription_id": str(
                    subscription.id
                ),
                "razorpay_subscription_id": (
                    subscription.razorpay_subscription_id
                ),
                "plan_id": str(plan.id),
                "plan_name": plan.name,
                "amount": str(plan.price),
                "currency": "INR"
            },
            description="Subscription created successfully"
        )










