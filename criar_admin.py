import os
import django
from django.contrib.auth import get_user_model

# Configura o ambiente Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "setup.settings")
django.setup()

User = get_user_model()

# Vai buscar as credenciais às variáveis de ambiente (ou usa valores padrão)
username = os.getenv("SUPER_USER_NAME", "admin")
password = os.getenv("SUPER_USER_PASSWORD", "Mauro2003") # Podes mudar isto aqui ou no Render
email = "wilson.goncalves07@gmail.com"

if not User.objects.filter(username=username).exists():
    print(f"A criar superuser: {username}...")
    User.objects.create_superuser(username=username, email=email, password=password)
    print("✅ Superuser criado com sucesso!")
else:
    print("ℹ️ Superuser já existe. Nada a fazer.")