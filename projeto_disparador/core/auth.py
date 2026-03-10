import jwt
from django.conf import settings
from ninja.security import HttpBearer
from ninja.errors import HttpError
from core.models import User

class JWTAuth(HttpBearer):
    def authenticate(self, request, token):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            user = User.objects.get(id=user_id)
            
            if not user.is_active:
                raise HttpError(403, "Account_disabled")
            if not user.is_approved:
                raise HttpError(403, "Account_pending_approval")
                
            return user
            
        except jwt.ExpiredSignatureError:
            raise HttpError(401, "Token_expired")
        except jwt.DecodeError:
            raise HttpError(401, "Invalid_token")
        except User.DoesNotExist:
            raise HttpError(401, "User_not_found")