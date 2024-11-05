# forms.py
from django import forms
from .models import Cliente

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['rut', 'nombre', 'apellido', 'fecha_nacimiento', 'genero', 'email', 'telefono', 'direccion']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'genero': forms.Select(choices=[('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')]),
        }
