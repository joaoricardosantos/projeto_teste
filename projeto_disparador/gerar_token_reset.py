import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from core.models import User, PasswordResetToken
import secrets

email = sys.argv[1] if len(sys.argv) > 1 else 'admin@admin.com'

try:
    user = User.objects.get(email=email)
except User.DoesNotExist:
    print(f"Usuário {email} não encontrado.")
    sys.exit(1)

PasswordResetToken.objects.filter(user=user, used=False).update(used=True)
token = secrets.token_urlsafe(32)
PasswordResetToken.objects.create(user=user, token=token)

print(f"\nLink de reset para {email}:")
print(f"http://localhost:3000/reset-password?token={token}\n")
