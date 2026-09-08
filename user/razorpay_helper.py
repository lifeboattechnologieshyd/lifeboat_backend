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