from django import forms
from .models import PedidoAlmuerzo, PedidoSopa, PedidoSegundo

class AlmuerzoForm(forms.ModelForm):
    class Meta:
        model = PedidoAlmuerzo
        fields = ['sopa', 'segundo', 'jugo', 'postre', 'cantidad']
        widgets = {
            'sopa': forms.Select(attrs={'class': 'form-select select2'}),
            'segundo': forms.Select(attrs={'class': 'form-select select2'}),
            'jugo': forms.Select(attrs={'class': 'form-select select2'}),
            'postre': forms.TextInput(attrs={'class': 'form-control'}),  # Usamos TextInput
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class SopaForm(forms.ModelForm):
    class Meta:
        model = PedidoSopa
        fields = ['sopa', 'jugo', 'postre', 'cantidad']
        widgets = {
            'sopa': forms.Select(attrs={'class': 'form-select select2'}),
            'jugo': forms.Select(attrs={'class': 'form-select select2'}),
            'postre': forms.TextInput(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class SegundoForm(forms.ModelForm):
    class Meta:
        model = PedidoSegundo
        fields = ['segundo', 'jugo', 'postre', 'cantidad']
        widgets = {
            'segundo': forms.Select(attrs={'class': 'form-select select2'}),
            'jugo': forms.Select(attrs={'class': 'form-select select2'}),
            'postre': forms.TextInput(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
        }
  