from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Chamado


class CadastroForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class ChamadoForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = ['titulo', 'categoria', 'prioridade', 'descricao']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'placeholder': 'Resumo do problema',
                'required': True
            }),
            'categoria': forms.Select(attrs={
                'required': True
            }),
            'prioridade': forms.Select(),
            'descricao': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Descreva o que aconteceu...',
                'required': True
            }),
        }
        labels = {
            'titulo': 'Título do Problema *',
            'categoria': 'Categoria *',
            'prioridade': 'Prioridade (Opcional)',
            'descricao': 'Descrição Detalhada *',
        }