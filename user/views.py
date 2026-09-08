import hashlib

from django.utils import timezone
from rest_framework.views import APIView

from db.models import UserMaster, MagicLoginToken
from shared.utils import CustomResponse, send_magic_login_link


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

            return CustomResponse.successResponse(
                data={
                    "user_id": str(user.id),
                    "email": user.email,
                    "is_new_user": True
                },
                description="Email verified successfully"
            )
        else:
            return CustomResponse.errorResponse(data={}, description="Link Expired or Invalid, Please try again")






