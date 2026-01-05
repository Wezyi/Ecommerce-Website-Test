from django import forms
from .models import Avaliacao

class AvaliacaoForm(forms.ModelForm):
    class Meta:
        model = Avaliacao
        fields = ['estrelas', 'comentario']
        widgets = {
            'comentario': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'O que achaste deste produto?'}),
            'estrelas': forms.Select(attrs={'class': 'form-select'}),
        }