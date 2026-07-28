from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from django.conf import settings


def verify_google_token(token: str) -> dict:
    idinfo = id_token.verify_oauth2_token(
        token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
    )
    return {
        "email": idinfo["email"],
        "google_id": idinfo["sub"],
        "full_name": idinfo.get("name", ""),
        "avatar_url": idinfo.get("picture", ""),
    }