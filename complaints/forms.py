from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Complaint

class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['name','phone','location','description','image']
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control','placeholder':'Full name'}),
            'phone': forms.TextInput(attrs={'class':'form-control','placeholder':'Phone number'}),
            'location': forms.TextInput(attrs={'class':'form-control','placeholder':'Location / Address'}),
            'description': forms.Textarea(attrs={'class':'form-control','rows':4,'placeholder':'Describe the issue in detail...'}),
            'image': forms.ClearableFileInput(attrs={'class':'form-control'})
        }

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class':'form-control','placeholder':'Email address'}))

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
