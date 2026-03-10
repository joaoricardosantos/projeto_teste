import jwt
from datetime import datetime, timedelta, timezone
from django.conf import settings

def create_access_token(user_id: str) -> str:
    payload = {
        "user_id": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=12),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")