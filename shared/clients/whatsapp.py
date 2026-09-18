import requests

from django.conf import settings


def get_number_id():
    url = "https://sms.lifeboattechnologies.com/dev/dlt_manager/whatsapp?type=number"
    headers = {
        "accept": "application/json",
        "Authorization": settings.WHATSAPP_API_KEY
    }
    response = requests.get(url, headers=headers)
    print(response.json())
    return response.json()



# testing ------
def login_logic():
    resp = get_number_id()
    if resp.get("success"):
        data = resp.get("data")
        data = data[0]
        phone_number_id= data["phone_number_id"]
        number = 9014083090
        send_otp(phone_number_id, number)


def send_otp(number_id=3094807680754266, number=9014083090, otp=1234):
    url = f"https://sms.lifeboattechnologies.com/dev/whatsapp?message_id=11861&phone_number_id={number_id}&numbers={number}&variables_values={otp}"
    headers = {
        "accept": "application/json",
        "Authorization": settings.WHATSAPP_API_KEY
    }
    response = requests.get(url, headers=headers)
    print(response.json())
    print(response.text)


def whatsapp_login_magic_link(token, mobile):
    url = "https://sms.lifeboattechnologies.com/dev/whatsapp/v26.0/3094807680754266/messages"
    payload = {
        "messaging_product": "whatsapp",
        "type": "template",
        "template": {
            "language": {"code": "en"},
            "name": "signin_request_dynamic",
            "components": [
                {
                    "type": "button",
                    "sub_type": "url",
                    "index": "0",
                    "parameters": [
                        {
                            "type": "payload",
                            "payload": f"{token}"
                        }
                    ]
                }
            ]
        },
        "recipient_type": "individual",
        "to": mobile
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": settings.WHATSAPP_API_KEY
    }
    response = requests.post(url, json=payload, headers=headers)
    print(response.text)