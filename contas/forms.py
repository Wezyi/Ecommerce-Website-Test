from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class RegistroUsuarioForm(UserCreationForm):
    # Adicionamos o campo email e dizemos que é obrigatório (required=True)
    email = forms.EmailField(required=True, help_text='Um endereço de email válido e real.')

    class Meta:
        model = User
        # Aqui definimos a ordem dos campos no site
        fields = ('username', 'email')
    
class EditarPerfilForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name'] # Podes adicionar Nome e Apelido se quiseres
        help_texts = {
            'username': None, # Remove o texto de ajuda chato do username
        }