import requests

TEXTLOCAL_API_KEY = "YOUR_TEXTLOCAL_API_KEY"
SENDER = "TXTLCL"  # default sender ID

def send_sms(mobile, message):
    url = "https://api.textlocal.in/send/"

    data = {
        'apikey': TEXTLOCAL_API_KEY,
        'numbers': mobile,
        'message': message,
        'sender': SENDER
    }

    response = requests.post(url, data=data)
    return response.json()
