import base64
import json
import time

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from django.conf import settings


def _cloudfront_safe_base64(data):
    """
    CloudFront uses URL-safe Base64 without = padding.
    """
    return (
        base64.b64encode(data)
        .decode("utf-8")
        .replace("+", "-")
        .replace("=", "_")
        .replace("/", "~")
    )


def generate_cloudfront_signed_cookies(
    resource_path,
    expires_in=3600,
):
    """
    Generate CloudFront signed cookies for a specific resource path.

    Example resource_path:
        https://d2lwfle8y9frks.cloudfront.net/hls/course-id/*
    """

    expires_at = int(time.time()) + expires_in

    policy = {
        "Statement": [
            {
                "Resource": resource_path,
                "Condition": {
                    "DateLessThan": {
                        "AWS:EpochTime": expires_at
                    }
                },
            }
        ]
    }

    policy_json = json.dumps(
        policy,
        separators=(",", ":")
    )

    private_key = serialization.load_pem_private_key(
        settings.AWS_CLOUDFRONT_PRIVATE_KEY.encode("utf-8"),
        password=None,
    )

    signature = private_key.sign(
        policy_json.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA1(),
    )

    encoded_policy = _cloudfront_safe_base64(
        policy_json.encode("utf-8")
    )

    encoded_signature = _cloudfront_safe_base64(
        signature
    )

    return {
        "CloudFront-Policy": encoded_policy,
        "CloudFront-Key-Pair-Id": settings.AWS_CLOUDFRONT_KEY_PAIR_ID,
        "CloudFront-Signature": encoded_signature,
        "expires_at": expires_at,
    }