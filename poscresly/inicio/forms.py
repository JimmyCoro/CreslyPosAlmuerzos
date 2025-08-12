from django import forms
from menu.models import MenuDia, MenuDiaSopa, MenuDiaSegundo, MenuDiaJugo

class MenuDiaForm(forms.ModelForm):
    class Meta:
        model = MenuDia
        fields = ['postre']
        widgets = {
            'postre': forms.Select(attrs={'class': 'form-select select2'})
        }

class MenuDiaSopaForm(forms.ModelForm):
    class Meta:
        model = MenuDiaSopa
        fields = ['sopa', 'cantidad']
        widgets = {
            'sopa': forms.Select(attrs={'class': 'form-select select2'}),
            'data-placeholder': 'Seleccionar Sopa',
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),

        }

class MenuDiaSegundoForm(forms.ModelForm):
    class Meta:
        model = MenuDiaSegundo
        fields = ['segundo', 'cantidad']
        widgets = {
            'segundo': forms.Select(attrs={'class': 'form-select select2'}),
            'data-placeholder': 'Seleccionar Segundo',
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),

        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['segundo'].required = False
        self.fields['cantidad'].required = False

class MenuDiaJugoForm(forms.ModelForm):
    class Meta:
        model = MenuDiaJugo
        fields = ['jugo']
        widgets = {
            'jugo': forms.Select(attrs={'class': 'form-select select2'})
        }

