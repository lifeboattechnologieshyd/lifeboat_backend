import razorpay
from django.conf import settings

def get_razorpay_client():
    print("RAZORPAY_KEY_ID:", getattr(settings, "RAZORPAY_KEY_ID", None))
    print("RAZORPAY_KEY_SECRET:", getattr(settings, "RAZORPAY_KEY_SECRET", None))
    return razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET,
        )
    )


def create_razorpay_subscription(plan_id):
    client = get_razorpay_client()
    return client.subscription.create({
        "plan_id": plan_id,
        "customer_notify": 1,
        "total_count": 120,
    })

def verify_signature(body, signature):
    client = get_razorpay_client()
    try:
        client.utility.verify_webhook_signature(
            body,
            signature,
            settings.RAZORPAY_WEBHOOK_SECRET,
        )
        print("Webhook Signature Verified")
        return True
    except Exception as e:
        print("error in verifying signature from webhook")
        print(e)
        return None


