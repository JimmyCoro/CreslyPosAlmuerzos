from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q

from .models import PerfilUsuario
from .permisos import GRUPO_ADMIN, GRUPO_EMPLEADO, ROLES, rol_de

User = get_user_model()


# La app corre con LANGUAGE_CODE='en-us' (cambiarlo alteraría el formato de
# los montos), así que los mensajes de los validadores se traducen aquí.
MENSAJES_PASSWORD = {
    'password_too_short': 'Muy corta: usa al menos 8 caracteres.',
    'password_too_similar': 'Se parece demasiado al nombre o al usuario.',
    'password_too_common': 'Es una contraseña demasiado común.',
    'password_entirely_numeric': 'No puede ser solo números.',
    'password_mismatch': 'Las dos contraseñas no coinciden.',
}


def validar_password_es(password, user=None):
    try:
        validate_password(password, user)
    except forms.ValidationError as e:
        raise forms.ValidationError([MENSAJES_PASSWORD.get(err.code, err.messages[0]) for err in e.error_list])


class CambiarPasswordForm(forms.Form):
    """Contraseña propia, escrita dos veces. Mismos nombres de campo que el
    SetPasswordForm de Django, pero con los errores en español."""
    new_password1 = forms.CharField(strip=False)
    new_password2 = forms.CharField(strip=False)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('new_password1')
        p2 = cleaned.get('new_password2')
        if p1 and p2 and p1 != p2:
            self.add_error('new_password2', MENSAJES_PASSWORD['password_mismatch'])
        elif p1:
            try:
                validar_password_es(p1, self.user)
            except forms.ValidationError as e:
                self.add_error('new_password1', e)
        return cleaned

    def save(self):
        self.user.set_password(self.cleaned_data['new_password1'])
        self.user.save()
        return self.user


def _admins_activos():
    return User.objects.filter(is_active=True).filter(Q(is_superuser=True) | Q(groups__name=GRUPO_ADMIN)).distinct()


def asignar_rol(user, rol):
    grupos = Group.objects.filter(name__in=[GRUPO_ADMIN, GRUPO_EMPLEADO])
    user.groups.remove(*grupos)
    grupo, _ = Group.objects.get_or_create(name=rol)
    user.groups.add(grupo)


def marcar_password_temporal(user):
    PerfilUsuario.objects.update_or_create(user=user, defaults={'debe_cambiar_password': True})


class _CampoPasswordMixin:
    def _validar_password(self, user):
        password = self.cleaned_data.get('password')
        if password:
            try:
                validar_password_es(password, user)
            except forms.ValidationError as e:
                self.add_error('password', e)
        return password


class UsuarioCrearForm(_CampoPasswordMixin, forms.ModelForm):
    rol = forms.ChoiceField(choices=ROLES, initial=GRUPO_EMPLEADO, widget=forms.RadioSelect)
    password = forms.CharField(
        label='Contraseña temporal', strip=False, widget=forms.TextInput(attrs={'autocomplete': 'off'}),
        help_text='Entrégasela al empleado. La cambiará en su primer ingreso.',
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username']
        labels = {'first_name': 'Nombre', 'last_name': 'Apellido', 'username': 'Usuario'}
        help_texts = {'username': 'Con esto ingresa. Sin espacios; letras, números y . _ -'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Ya existe un usuario con ese nombre')
        return username

    def clean(self):
        cleaned = super().clean()
        candidato = User(
            username=cleaned.get('username', ''), first_name=cleaned.get('first_name', ''),
            last_name=cleaned.get('last_name', ''),
        )
        self._validar_password(candidato)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.save()
        asignar_rol(user, self.cleaned_data['rol'])
        marcar_password_temporal(user)
        return user


class UsuarioEditarForm(forms.ModelForm):
    rol = forms.ChoiceField(choices=ROLES, widget=forms.RadioSelect)
    is_active = forms.BooleanField(label='Cuenta activa', required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name']
        labels = {'first_name': 'Nombre', 'last_name': 'Apellido'}

    def __init__(self, *args, editor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.editor = editor
        self.fields['first_name'].required = True
        self.fields['rol'].initial = rol_de(self.instance)
        self.fields['is_active'].initial = self.instance.is_active
        if self.instance.is_superuser:
            # El superusuario siempre es admin; no tiene sentido cambiarle el rol.
            del self.fields['rol']

    def clean(self):
        cleaned = super().clean()
        user = self.instance
        activo = cleaned.get('is_active', False)
        rol = cleaned.get('rol', GRUPO_ADMIN)
        if self.editor is not None and user.pk == self.editor.pk:
            if not activo:
                self.add_error('is_active', 'No puedes desactivar tu propia cuenta')
            if rol != GRUPO_ADMIN:
                self.add_error('rol', 'No puedes quitarte el rol de administrador')
        sigue_admin = activo and (user.is_superuser or rol == GRUPO_ADMIN)
        if not sigue_admin and not _admins_activos().exclude(pk=user.pk).exists():
            raise forms.ValidationError('Tiene que quedar al menos un administrador activo')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = self.cleaned_data['is_active']
        user.save()
        if 'rol' in self.cleaned_data:
            asignar_rol(user, self.cleaned_data['rol'])
        return user


class RestablecerPasswordForm(_CampoPasswordMixin, forms.Form):
    password = forms.CharField(
        label='Nueva contraseña temporal', strip=False, widget=forms.TextInput(attrs={'autocomplete': 'off'}),
        help_text='Al guardar se cierra su sesión en todos los equipos y tendrá que elegir una propia al entrar.',
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        cleaned = super().clean()
        self._validar_password(self.user)
        return cleaned

    def save(self):
        self.user.set_password(self.cleaned_data['password'])
        self.user.save()
        marcar_password_temporal(self.user)
        return self.user
