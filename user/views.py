import hashlib
import hmac
import json
import secrets

import razorpay
from django.conf import settings
from django.contrib.auth import authenticate
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from django.utils import timezone
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from db.models import UserMaster, MagicLoginToken, Plan, Subscription, PaymentTransaction, OTP
from shared.clients.aws.s3 import add_unique_suffix_to_filename, sanitize_filename
from shared.utils import CustomResponse, send_magic_login_link, otp_preparation_for_login
from user.razorpay_helper import create_razorpay_subscription, verify_signature, get_razorpay_client


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
        source = data.get("source", "mobile")
        user = UserMaster.objects.filter(email=email).first()
        if user:
            if not user.has_usable_password():
                otp_preparation_for_login(email)
                return CustomResponse.successResponse(data={
                    "is_login_flow": True,
                    "password_required": False,
                    "email": user.email
                }, description="OTP has been sent to email address")
            else:
                print("User exists so asking him password")
                return CustomResponse.successResponse(data={
                    "is_login_flow": True,
                    "password_required":True,
                    "email": user.email
                }, description="Please enter password")

        else:
            if source == "website":
                otp_preparation_for_login(email)
                return CustomResponse.successResponse(data={
                    "is_login_flow": True,
                    "password_required": False,
                }, description="OTP Mail sent successfully")
            print("user does not exists so sending an email")
            send_magic_login_link(email)
            return CustomResponse.successResponse(data={
                "is_login_flow":False,
            }, description="Mail sent successfully")


class VerifyOTP(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")
        if not email:
            return CustomResponse.errorResponse(
                description="Email is required"
            )
        if not otp:
            return CustomResponse.errorResponse(
                description="OTP is required"
            )
        email = email.strip().lower()
        otp_record = (
            OTP.objects
            .filter(
                email=email,
                verified_at__isnull=True
            )
            .order_by("-created_at")
            .first()
        )
        if not otp_record:
            return CustomResponse.errorResponse(
                description="Invalid OTP"
            )
        if otp_record.expires_at <= timezone.now():
            return CustomResponse.errorResponse(
                description="OTP has expired"
            )
        # if otp_record.attempts >= 5:
        #     return CustomResponse.errorResponse(
        #         description="Too many OTP attempts"
        #     )
        # -----------------------------------------
        # 5. Verify OTP
        # -----------------------------------------

        if otp != otp_record.otp:
            otp_record.attempts += 1
            otp_record.save(
                update_fields=[
                    "attempts"
                ]
            )
            return CustomResponse.errorResponse(
                description="Invalid OTP"
            )
        otp_record.verified_at = timezone.now()
        otp_record.save(
            update_fields=[
                "verified_at",
            ]
        )
        user = UserMaster.objects.filter(
            email=email
        ).first()
        if not user:
            user = UserMaster.objects.create(
                email=email,
                username=email.split("@")[0]
            )
            print(f"New user created: {user.id}")
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        return CustomResponse.successResponse(
            data={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "email": user.email,
            },
            description="Email verified successfully"
        )

class SetPassword(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        password = request.data.get("password")
        if not password:
            return CustomResponse.errorResponse(
                description="Password is required"
            )
        if len(password) < 8:
            return CustomResponse.errorResponse(
                description="Password must be at least 8 characters"
            )
        user.set_password(password)
        user.save(update_fields=["password"])
        return CustomResponse.successResponse(
            data={
                "password_set": True
            },
            description="Password set successfully"
        )

class Login(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        # -----------------------------------------
        # 1. Validate request
        # -----------------------------------------
        if not email:
            return CustomResponse.errorResponse(
                description="Email is required"
            )
        if not password:
            return CustomResponse.errorResponse(
                description="Password is required"
            )
        email = email.strip().lower()
        # -----------------------------------------
        # 2. Authenticate user
        # -----------------------------------------

        user = UserMaster.objects.filter(
            email=email
        ).first()


        if not user:
            return CustomResponse.errorResponse(
                description="Invalid email"
            )
        if not user.check_password(password):
            return CustomResponse.errorResponse(
                description="Invalid password"
            )
        # -----------------------------------------
        # 3. Check active user
        # -----------------------------------------
        if not user.is_active:
            return CustomResponse.errorResponse(
                description="Your account is inactive"
            )
        # -----------------------------------------
        # 4. Generate JWT
        # -----------------------------------------
        refresh = RefreshToken.for_user(user)
        subscription = Subscription.objects.filter(
                    user=user,
                    status="active"
                ).select_related("plan").order_by("-created_at").first()

        subscription_data = {
            "is_active": False
        }
        if subscription:
            subscription_data = {
                "is_active": True,
                "plan_code": subscription.plan.code,
                "plan_name": subscription.plan.name,
                "status": subscription.status,
                "start_at": subscription.start_at,
                "end_at": subscription.end_at,
                "next_billing_at": subscription.next_charge_at,
            }
        # -----------------------------------------
        # 5. Response
        # -----------------------------------------
        return CustomResponse.successResponse(
            data={
                "user_id": str(user.id),
                "email": user.email,
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "subscription":subscription_data
            },
            description="Login successful"
        )

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



class MySubscription(APIView):

    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        # -----------------------------------------
        # Get latest active subscription
        # -----------------------------------------
        subscription = (
            Subscription.objects
            .filter(
                user=user,
                status="active"
            )
            .select_related("plan")
            .order_by("-created_at")
            .first()
        )
        # -----------------------------------------
        # No active subscription
        # -----------------------------------------
        if not subscription:
            return CustomResponse.successResponse(
                data={
                    "is_subscribed": False,
                    "subscription": None
                },
                description="No active membership found"
            )

        # -----------------------------------------
        # Active subscription
        # -----------------------------------------

        return CustomResponse.successResponse(

            data={
                "is_subscribed": True,
                "subscription": {

                    "id": str(
                        subscription.id
                    ),

                    "razorpay_subscription_id": (
                        subscription.razorpay_subscription_id
                    ),

                    "plan": {

                        "id": str(
                            subscription.plan.id
                        ),

                        "code": (
                            subscription.plan.code
                        ),

                        "name": (
                            subscription.plan.name
                        ),

                        "price": str(
                            subscription.plan.price
                        ),

                        "billing_interval": (
                            subscription.plan.billing_interval
                        ),

                        "billing_interval_count": (
                            subscription.plan.billing_interval_count
                        )

                    },

                    "status": (
                        subscription.status
                    ),

                    "start_at": (
                        subscription.start_at
                    ),

                    "end_at": (
                        subscription.end_at
                    ),

                    "next_billing_at": (
                        subscription.next_billing_at
                    ),

                    "cancel_at_period_end": (
                        subscription.cancel_at_period_end
                    ),

                    "cancelled_at": (
                        subscription.cancelled_at
                    )
                }
            },

            description="Subscription details fetched successfully"
        )


class FileUploadView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        files = request.FILES.getlist("files")
        path = request.data.get("path", "temp")
        if not files:
            return CustomResponse.errorResponse(description="Files are empty")
        uploaded_files = []
        try:
            for file_obj in files:
                # Save each file to the default storage
                sanitized_filename = add_unique_suffix_to_filename(sanitize_filename(file_obj.name))
                file_path = default_storage.save(f"{path}/{sanitized_filename}", ContentFile(file_obj.read()))
                file_url = settings.MEDIA_URL + file_path
                uploaded_files.append(
                    {"original_filename": file_obj.name, "file_url": file_url, "file_path": file_path}
                )

            return CustomResponse().successResponse(uploaded_files)

        except Exception as e:
            return CustomResponse().errorResponse(
                description="File upload failed"
            )


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data
        if "username" in data:
            user.username = data["username"]
        if "image" in data:
            user.image = data["image"]
        if "bio" in data:
            user.bio = data["bio"]
        if "mobile" in data:
            user.bio = data["mobile"]
        user.save()
        return CustomResponse.successResponse(data={}, description="Profile Updated Successfully")


    def get(self, request):
        user = request.user
        resp = {
            "email": user.email,
            "bio": user.bio,
            "mobile": user.mobile,
            "username": user.username,
            "image": user.image,
        }
        return CustomResponse.successResponse(data=resp)

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
        ).first()
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

from datetime import datetime, timedelta


class Webhook(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print("\n========== RAZORPAY WEBHOOK ==========")
        body = request.body.decode("utf-8")
        signature = request.headers.get("X-Razorpay-Signature")
        verified = verify_signature(body, signature)
        if not verified:
            return CustomResponse.errorResponse(
                description="Signature Verification failed"\
            )
        data = json.loads(body)
        event = data.get("event")
        print("Event:", event)
        event_id = request.headers.get(
            "X-Razorpay-Event-Id"
        )
        print("Razorpay event ID:", event_id)
        # -----------------------------------------
        # 7. Handle events
        # -----------------------------------------

        if event == "subscription.activated":

            self.handle_subscription_activated(data)

        elif event == "subscription.charged":

            self.handle_subscription_charged(data)

        elif event == "subscription.cancelled":

            self.handle_subscription_cancelled(data)

        elif event == "subscription.completed":

            self.handle_subscription_completed(data)

        elif event == "subscription.halted":

            self.handle_subscription_halted(data)

        elif event == "subscription.paused":

            self.handle_subscription_paused(data)

        elif event == "subscription.resumed":

            self.handle_subscription_resumed(data)

        # elif event == "payment.captured":
        #
        #     self.handle_payment_captured(data)

        # elif event == "payment.failed":
        #
        #     self.handle_payment_failed(data)

        else:
            print(
                "Unhandled Razorpay webhook event:",
                event
            )
        # -----------------------------------------
        # 8. Always return 200 after successful
        #    signature verification
        # -----------------------------------------
        return CustomResponse.successResponse(
            data={
                "received": True
            },
            description="Webhook processed successfully"
        )

    def handle_subscription_activated(self, data):
        subscription_entity = data.get("payload", {}).get("subscription", {}).get("entity", {})
        if not subscription_entity:
            return CustomResponse().successResponse(
                data={},
                description="Subscription Entity not found"
            )
        razorpay_subscription_id = subscription_entity.get("id")
        subscription = Subscription.objects.filter(
            razorpay_subscription_id=razorpay_subscription_id
        ).first()
        if not subscription:
            return CustomResponse().successResponse(
                data={},
                description="Subscription not found"
            )
        # ---------------------------------------------------------
        # SUBSCRIPTION ACTIVATED
        # ---------------------------------------------------------
        subscription.status = "active"
        if subscription_entity.get("current_start"):
            subscription.starts_at = datetime.fromtimestamp(
                subscription_entity["current_start"],
                tz=timezone.get_current_timezone(),
            )
        if subscription_entity.get("current_end"):
            subscription.end_at = datetime.fromtimestamp(
                subscription_entity["current_end"],
                tz=timezone.get_current_timezone(),
            )
        if subscription_entity.get("charge_at"):
            subscription.next_charge_at = datetime.fromtimestamp(
                subscription_entity["charge_at"],
                tz=timezone.get_current_timezone(),
            )
        subscription.save(
            update_fields=[
                "status",
                "starts_at",
                "end_at",
                "next_charge_at",
            ]
        )
        print("Subscription activated:",razorpay_subscription_id)

    def handle_subscription_charged(self, data):
        subscription_data = data["payload"]["subscription"]["entity"]
        payment_data = data["payload"].get("payment", {}).get("entity")
        razorpay_subscription_id = subscription_data["id"]
        subscription = Subscription.objects.filter(
            razorpay_subscription_id=razorpay_subscription_id
        ).first()
        if not subscription:
            print(
                "Subscription not found:",
                razorpay_subscription_id
            )
            return
        # -----------------------------------------
        # Update subscription
        # -----------------------------------------
        subscription.status = "active"
        if subscription_data.get("current_start"):
            subscription.start_at = timezone.datetime.fromtimestamp(
                subscription_data["current_start"],
                tz=timezone.get_current_timezone()
            )
        if subscription_data.get("current_end"):
            subscription.end_at = timezone.datetime.fromtimestamp(
                subscription_data["current_end"],
                tz=timezone.get_current_timezone()
            )
        if subscription_data.get("charge_at"):
            subscription.next_charge_at = datetime.fromtimestamp(
                subscription_data["charge_at"],
                tz=timezone.get_current_timezone(),
            )
        subscription.save(
            update_fields=[
                "status",
                "start_at",
                "end_at",
                "next_charge_at"
            ]
        )
        # -----------------------------------------
        # Save payment
        # -----------------------------------------
        if payment_data:
            razorpay_payment_id = payment_data["id"]
            payment_transaction = PaymentTransaction.objects.filter(
                razorpay_payment_id=razorpay_payment_id
            ).first()
            if not payment_transaction:
                PaymentTransaction.objects.create(
                    user=subscription.user,
                    subscription=subscription,
                    plan=subscription.plan,
                    amount=payment_data["amount"] / 100,
                    currency=payment_data.get(
                        "currency",
                        "INR"
                    ),
                    razorpay_payment_id=razorpay_payment_id,
                    razorpay_subscription_id=razorpay_subscription_id,
                    status="captured"
                )
                print(
                    "Payment transaction created:",
                    razorpay_payment_id
                )
            else:
                print(
                    "Payment already exists:",
                    razorpay_payment_id
                )

    def handle_subscription_cancelled(self, data):
        subscription_data = data["payload"]["subscription"]["entity"]
        razorpay_subscription_id = subscription_data["id"]
        subscription = Subscription.objects.filter(
            razorpay_subscription_id=razorpay_subscription_id
        ).first()
        if not subscription:
            return
        subscription.status = "cancelled"
        subscription.cancelled_at = timezone.now()
        subscription.save(
            update_fields=[
                "status",
                "cancelled_at",
            ]
        )
        print("Subscription cancelled:",razorpay_subscription_id)

    def handle_subscription_completed(self, data):

        subscription_data = data["payload"]["subscription"]["entity"]

        razorpay_subscription_id = subscription_data["id"]

        subscription = Subscription.objects.filter(
            razorpay_subscription_id=razorpay_subscription_id
        ).first()

        if not subscription:
            return

        subscription.status = "expired"

        subscription.save(
            update_fields=[
                "status",
            ]
        )

        print(
            "Subscription completed:",
            razorpay_subscription_id
        )

    def handle_subscription_halted(self, data):

        subscription_data = data["payload"]["subscription"]["entity"]

        razorpay_subscription_id = subscription_data["id"]

        subscription = Subscription.objects.filter(
            razorpay_subscription_id=razorpay_subscription_id
        ).first()

        if not subscription:
            return

        subscription.status = "failed"

        subscription.save(
            update_fields=[
                "status",
            ]
        )

        print(
            "Subscription halted:",
            razorpay_subscription_id
        )

    def handle_subscription_paused(self, data):

        subscription_data = data["payload"]["subscription"]["entity"]

        razorpay_subscription_id = subscription_data["id"]

        subscription = Subscription.objects.filter(
            razorpay_subscription_id=razorpay_subscription_id
        ).first()

        if not subscription:
            return

        subscription.status = "paused"

        subscription.save(
            update_fields=[
                "status",
            ]
        )

    def handle_subscription_resumed(self, data):
        subscription_data = data["payload"]["subscription"]["entity"]
        razorpay_subscription_id = subscription_data["id"]
        subscription = Subscription.objects.filter(
            razorpay_subscription_id=razorpay_subscription_id
        ).first()
        if not subscription:
            return

        subscription.status = "active"
        subscription.save(
            update_fields=[
                "status",
            ]
        )

    # def handle_payment_failed(self, data):
    #
    #     payment_data = data["payload"]["payment"]["entity"]
    #
    #     razorpay_payment_id = payment_data["id"]
    #
    #     payment_transaction = PaymentTransaction.objects.filter(
    #         razorpay_payment_id=razorpay_payment_id
    #     ).first()
    #
    #     if payment_transaction:
    #         payment_transaction.status = "failed"
    #         payment_transaction.save(
    #             update_fields=[
    #                 "status",
    #                 "updated_at"
    #             ]
    #         )
    #
    #         print(
    #             "Payment marked failed:",
    #             razorpay_payment_id
    #         )
    #
    #     else:
    #         print(
    #             "Failed payment transaction not found:",
    #             razorpay_payment_id
    #         )

class VerifySubscriptionPaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        razorpay_payment_id = request.data.get(
            "razorpay_payment_id"
        )

        razorpay_subscription_id = request.data.get(
            "razorpay_subscription_id"
        )

        razorpay_signature = request.data.get(
            "razorpay_signature"
        )

        # -----------------------------------------
        # 1. Validate request
        # -----------------------------------------

        if not razorpay_payment_id:
            return CustomResponse.errorResponse(
                description="Razorpay payment ID is required"
            )

        if not razorpay_subscription_id:
            return CustomResponse.errorResponse(
                description="Razorpay subscription ID is required"
            )

        if not razorpay_signature:
            return CustomResponse.errorResponse(
                description="Razorpay signature is required"
            )

        # -----------------------------------------
        # 2. Find our subscription
        # -----------------------------------------

        subscription = Subscription.objects.filter(
            razorpay_subscription_id=razorpay_subscription_id,
            user=user
        ).select_related(
            "plan"
        ).first()

        if not subscription:
            return CustomResponse.errorResponse(
                description="Subscription not found"
            )
        # -----------------------------------------
        # 3. Verify Razorpay signature
        #
        # For subscriptions:
        # payment_id + "|" + subscription_id
        # -----------------------------------------

        message = (
                razorpay_payment_id
                + "|"
                + razorpay_subscription_id
        )

        generated_signature = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(
                generated_signature,
                razorpay_signature
        ):
            return CustomResponse.errorResponse(
                description="Invalid payment signature"
            )

        # -----------------------------------------
        # 4. Fetch latest payment status
        #    directly from Razorpay
        # -----------------------------------------

        client = razorpay.Client(
            auth=(
                settings.RAZORPAY_KEY_ID,
                settings.RAZORPAY_KEY_SECRET
            )
        )

        try:
            payment = client.payment.fetch(
                razorpay_payment_id
            )
        except Exception as e:
            print(
                "Razorpay payment fetch error:",
                str(e)
            )
            return CustomResponse.errorResponse(
                description="Unable to verify payment with Razorpay"
            )
        payment_status = payment.get("status")
        if payment_status != "captured":
            return CustomResponse.errorResponse(
                description=f"Payment is not captured. Current status: {payment_status}"
            )
            # -----------------------------------------
            # 6. Validate currency
            # -----------------------------------------

        payment_currency = payment.get("currency")

        if payment_currency != "INR":
            return CustomResponse.errorResponse(
                    description="Invalid payment currency"
                )

        # -----------------------------------------
        # 7. Validate amount
        # -----------------------------------------

        razorpay_amount = payment.get("amount")

        expected_amount = int(
            subscription.plan.price * 100
        )

        if razorpay_amount != expected_amount:

            print(
                "Payment amount mismatch:",
                razorpay_amount,
                expected_amount
            )

            return CustomResponse.errorResponse(
                description="Payment amount mismatch"
            )
        with transaction.atomic():

            payment_transaction = (
                PaymentTransaction.objects.filter(
                    razorpay_payment_id=razorpay_payment_id
                ).first()
            )

            if payment_transaction:
                # ---------------------------------
                # Payment may have already been
                # saved by webhook
                # ---------------------------------

                payment_transaction.status = "captured"

                payment_transaction.razorpay_signature = (
                    razorpay_signature
                )

                payment_transaction.save(
                    update_fields=[
                        "status",
                        "razorpay_signature",
                        "updated_at"
                    ]
                )

                print(
                    "Payment transaction already exists:",
                    razorpay_payment_id
                )
            else:

                payment_transaction = (
                    PaymentTransaction.objects.create(

                        user=user,

                        subscription=subscription,

                        plan=subscription.plan,

                        amount=(
                                razorpay_amount / 100
                        ),

                        currency=payment_currency,

                        razorpay_payment_id=(
                            razorpay_payment_id
                        ),

                        razorpay_subscription_id=(
                            razorpay_subscription_id
                        ),

                        razorpay_signature=(
                            razorpay_signature
                        ),

                        status="captured"
                    )
                )

                print(
                    "Payment transaction created:",
                    razorpay_payment_id
                )

        # -----------------------------------------
        # 9. Return success
        # -----------------------------------------

        return CustomResponse.successResponse(

            data={

                "payment_verified": True,

                "payment_id": (
                    razorpay_payment_id
                ),

                "subscription_id": (
                    str(subscription.id)
                ),

                "razorpay_subscription_id": (
                    razorpay_subscription_id
                ),

                "payment_status": payment_status,

                "amount": (
                        razorpay_amount / 100
                ),

                "currency": payment_currency
            },

            description="Payment verified successfully"
        )
