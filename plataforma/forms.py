from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm, SetPasswordForm, PasswordResetForm, UsernameField
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

class RegistrationForm(UserCreationForm):
  password1 = forms.CharField(
      label=_("Password"),
      widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Senha'}),
  )
  password2 = forms.CharField(
      label=_("Password Confirmation"),
      widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repetir senha'}),
  )

  class Meta:
    model = User
    fields = ('username', 'email', )

    widgets = {
      'username': forms.TextInput(attrs={
          'class': 'form-control',
          'placeholder': 'Nome de usuário'
      }),
      'email': forms.EmailInput(attrs={
          'class': 'form-control',
          'placeholder': 'E-mail'
      })
    }

class LoginForm(AuthenticationForm):
    username = UsernameField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Nome de usuário ou e-mail'
    }))
    password = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Senha'
    }))


class UserPasswordResetForm(PasswordResetForm):
  email = forms.EmailField(widget=forms.EmailInput(attrs={
    'class': 'form-control',
    'placeholder': 'E-mail'
  }))

class UserSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Nova senha'
    }), label="Nova senha")
    new_password2 = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirmar nova senha'
    }), label="Confirmar nova senha")
    

class UserPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Senha Antiga'
    }), label='Senha Antiga')
    new_password1 = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Nova senha'
    }), label="Nova senha")
    new_password2 = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirmar nova senha'
    }), label="Confirmar nova senha")

class SiloForm(forms.Form):
    id_silo = forms.IntegerField(required=False)
    identificacao = forms.CharField(max_length=255, required=True)
    observacao = forms.CharField(max_length=255, required=False)
    status = forms.CharField(max_length=255, required=True)

class SensorForm(forms.Form):
    id_sensor = forms.IntegerField(required=False)
    nome = forms.CharField(max_length=255, required=True)
    tipo = forms.CharField(max_length=45, required=True)
    status = forms.CharField(max_length=255, required=True)
    observacao = forms.CharField(max_length=255, required=False)


class ControladorForm(forms.Form):
    id_sensor = forms.IntegerField(required=False)
    nome = forms.CharField(max_length=255, required=True)
    tipo = forms.CharField(max_length=45, required=True)
    status = forms.CharField(max_length=255, required=True)
    observacao = forms.CharField(max_length=255, required=False)

class AeracaoSiloForm(forms.Form):
    volume = forms.FloatField(label='Volume do Silo em m³', required=False)
    temperatura_inicial = forms.FloatField(label='Temperatura Desejada em °C', required=False)
    temperatura_desejada = forms.FloatField(label='Temperatura Desejada em °C', required=True)
    umidade_inicial = forms.FloatField(label='Umidade Relativa Inicial em %', required=False)
    umidade_desejada = forms.FloatField(label='Umidade Relativa Desejada em %', required=False)
    taxa_fluxo_ar = forms.FloatField(label='Taxa de Fluxo de Ar em m³/s', required=False)






