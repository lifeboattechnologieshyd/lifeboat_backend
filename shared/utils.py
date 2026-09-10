import hashlib
import secrets
from datetime import timedelta

import requests
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework.response import Response

from rest_framework import status

from db.models import MagicLoginToken, OTP


########################
#    CUSTOM RESPONSE   #
########################


class CustomResponse:

    @staticmethod
    def successResponse(
        data, errorCode=0, description="Request Successful", total=0, status=status.HTTP_200_OK, **kwargs
    ):
        return Response(
            {
                "success": True,
                "errorCode": errorCode,
                "description": description,
                "total": total,
                **kwargs,
                "data": data,
            },
            status=status,
        )

    @staticmethod
    def errorResponse(
        data=None,
        errorCode=0,
        description="Request Failed",
        total=0,
        status=status.HTTP_200_OK,
        **kwargs,
    ):
        if data is None:
            data = {}
        return Response(
            {
                "success": False,
                "errorCode": errorCode,
                "description": description,
                "total": total,
                "data": data,
                **kwargs,
            },
            status=status,
        )

def send_magic_login_link(email):
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(
        raw_token.encode()
    ).hexdigest()
    expires_at = timezone.now() + timedelta(minutes=15)
    MagicLoginToken.objects.filter(
        email=email,
        used_at__isnull=True
    ).update(
        used_at=timezone.now()
    )
    MagicLoginToken.objects.create(
        email=email,
        token_hash=token_hash,
        expires_at=expires_at
    )
    magic_link = f"{settings.FRONTEND_URL}/email-verification/{raw_token}/"
    context = {
        "magic_link": magic_link
    }
    send_otp_email(email, "emails/magic_email.html", context, f"Login to Lifeboat")



def otp_preparation_for_login(email):
    otp = str(
        secrets.randbelow(1000000)
    ).zfill(6)
    expires_at = timezone.now() + timedelta(minutes=10)
    OTP.objects.filter(
        email=email,
        verified_at__isnull=True
    ).update(
        expires_at=timezone.now()
    )
    OTP.objects.create(
        email=email,
        otp=otp,
        expires_at=expires_at
    )
    context = {
        "otp": otp
    }
    send_otp_email(email, "emails/otp_email.html", context, f"Your Lifeboat verification code")


def send_otp_email(email, template, context, subject):
    url = settings.ISHVAA_BASE_URL
    headers = {
        'X-API-Key': settings.ISHVAA_EMAIL_API_KEY,
        'Content-Type': 'application/json'
    }
    html_content = render_to_string(
        template,
        context
    )
    payload = {
        "from_name": "Lifeboat",
        "from": "noreply@lifeboattechnologies.com",
        "to": [
            email
        ],
        "subject": subject,
        "html": html_content
    }
    response = requests.post(url, headers=headers, json=payload)
    print("Mail status:", response.json())

