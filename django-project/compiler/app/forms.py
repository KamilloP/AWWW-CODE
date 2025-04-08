from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms
 
class SignUpForm(UserCreationForm):
    name = forms.CharField(max_length=11)
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', )
        labels = {'name': 'name',}
