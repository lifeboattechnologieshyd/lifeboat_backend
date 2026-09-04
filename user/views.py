from rest_framework.views import APIView

from db.models import UserMaster
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





