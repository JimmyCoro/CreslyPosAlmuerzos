from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import PerfilUsuario
from .permisos import GRUPO_ADMIN, GRUPO_EMPLEADO

User = get_user_model()
CLAVE = 'Pizza-segura-2026'


@override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class UsuariosYAccesoTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user('dueno', password=CLAVE, first_name='Dueño')
        self.admin.groups.add(Group.objects.get(name=GRUPO_ADMIN))
        self.empleado = User.objects.create_user('ana', password=CLAVE, first_name='Ana')
        self.empleado.groups.add(Group.objects.get(name=GRUPO_EMPLEADO))

    # ----- Login obligatorio -----

    def test_anonimo_va_al_login_en_toda_la_app(self):
        for ruta in ['/', '/caja/', '/menu/', '/pizzeria/', '/pizzeria/caja/turno/', reverse('usuarios')]:
            r = self.client.get(ruta)
            self.assertEqual(r.status_code, 302, ruta)
            self.assertTrue(r['Location'].startswith('/login/?next='), ruta)

    def test_anonimo_en_ajax_recibe_401_json(self):
        r = self.client.post(reverse('guardar_pedido'), '{}', content_type='application/json')
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()['login_url'], reverse('login'))
        r = self.client.get(reverse('obtener_contadores_tabs'))
        self.assertEqual(r.status_code, 401)

    def test_login_publico_y_respeta_next(self):
        self.assertEqual(self.client.get(reverse('login')).status_code, 200)
        r = self.client.post(reverse('login'), {'username': 'ana', 'password': CLAVE, 'next': '/menu/'})
        self.assertRedirects(r, '/menu/', fetch_redirect_response=False)

    def test_next_externo_se_ignora(self):
        r = self.client.post(reverse('login'), {'username': 'ana', 'password': CLAVE, 'next': 'https://malo.com/'})
        self.assertEqual(r['Location'], '/pizzeria/')

    def test_clave_incorrecta_y_cuenta_desactivada(self):
        r = self.client.post(reverse('login'), {'username': 'ana', 'password': 'otra'})
        self.assertContains(r, 'Usuario o contraseña incorrectos')
        self.empleado.is_active = False
        self.empleado.save()
        r = self.client.post(reverse('login'), {'username': 'ana', 'password': CLAVE})
        self.assertContains(r, 'Usuario o contraseña incorrectos')

    def test_logout_solo_por_post(self):
        self.client.force_login(self.empleado)
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        self.client.post(reverse('logout'))
        self.assertEqual(self.client.get('/menu/').status_code, 302)

    def test_login_antiguo_de_pizzeria_redirige(self):
        r = self.client.get('/pizzeria/login/')
        self.assertRedirects(r, reverse('login'), fetch_redirect_response=False)

    # ----- Roles -----

    def test_empleado_no_entra_a_pantallas_de_admin(self):
        self.client.force_login(self.empleado)
        for ruta in [reverse('usuarios'), reverse('menu_configurar'), reverse('pizzeria_gestionar_mesas'),
                     reverse('pizzeria_caja_cerrar')]:
            self.assertEqual(self.client.get(ruta).status_code, 403, ruta)
        r = self.client.post(reverse('menu_publicar'), '{}', content_type='application/json')
        self.assertEqual(r.status_code, 403)
        self.assertIn('error', r.json())

    def test_admin_si_entra(self):
        self.client.force_login(self.admin)
        for ruta in [reverse('usuarios'), reverse('usuario_crear'), reverse('menu_configurar'),
                     reverse('pizzeria_gestionar_mesas')]:
            self.assertEqual(self.client.get(ruta).status_code, 200, ruta)

    def test_empleado_si_puede_operar(self):
        self.client.force_login(self.empleado)
        for ruta in ['/', '/menu/', reverse('pizzeria_mapa_mesas'), reverse('pizzeria_caja_abrir')]:
            self.assertEqual(self.client.get(ruta).status_code, 200, ruta)

    # ----- Gestión de usuarios -----

    def test_crear_usuario_obliga_a_cambiar_la_clave(self):
        self.client.force_login(self.admin)
        r = self.client.post(reverse('usuario_crear'), {
            'first_name': 'Luis', 'last_name': 'Mora', 'username': 'luis',
            'rol': GRUPO_EMPLEADO, 'password': 'Temporal-1234',
        })
        self.assertRedirects(r, reverse('usuarios'))
        luis = User.objects.get(username='luis')
        self.assertTrue(luis.groups.filter(name=GRUPO_EMPLEADO).exists())
        self.assertTrue(luis.perfil.debe_cambiar_password)

        self.client.post(reverse('logout'))
        r = self.client.post(reverse('login'), {'username': 'luis', 'password': 'Temporal-1234'})
        self.assertRedirects(r, reverse('cambiar_password'), fetch_redirect_response=False)
        # Mientras no la cambie, todo lo manda de vuelta a cambiar la clave.
        self.assertRedirects(self.client.get('/menu/'), reverse('cambiar_password'), fetch_redirect_response=False)

        r = self.client.post(reverse('cambiar_password'), {
            'new_password1': 'MiClavePropia-99', 'new_password2': 'MiClavePropia-99',
        })
        self.assertRedirects(r, '/pizzeria/', fetch_redirect_response=False)
        self.assertEqual(self.client.get('/menu/').status_code, 200)
        luis.perfil.refresh_from_db()
        self.assertFalse(luis.perfil.debe_cambiar_password)

    def test_clave_debil_muestra_error_en_espanol(self):
        self.client.force_login(self.admin)
        r = self.client.post(reverse('usuario_crear'), {
            'first_name': 'Luis', 'username': 'luis', 'rol': GRUPO_EMPLEADO, 'password': '1234',
        })
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Muy corta')
        self.assertFalse(User.objects.filter(username='luis').exists())

    def test_usuario_repetido(self):
        self.client.force_login(self.admin)
        r = self.client.post(reverse('usuario_crear'), {
            'first_name': 'Otra', 'username': 'ANA', 'rol': GRUPO_EMPLEADO, 'password': 'Temporal-1234',
        })
        self.assertContains(r, 'Ya existe un usuario con ese nombre')

    def test_restablecer_clave(self):
        self.client.force_login(self.admin)
        r = self.client.post(reverse('usuario_password', args=[self.empleado.pk]), {'password': 'Nueva-Temporal-55'})
        self.assertRedirects(r, reverse('usuarios'))
        self.empleado.refresh_from_db()
        self.assertTrue(self.empleado.check_password('Nueva-Temporal-55'))
        self.assertTrue(PerfilUsuario.objects.get(user=self.empleado).debe_cambiar_password)

    def test_desactivar_empleado(self):
        self.client.force_login(self.admin)
        r = self.client.post(reverse('usuario_editar', args=[self.empleado.pk]), {
            'first_name': 'Ana', 'last_name': '', 'rol': GRUPO_EMPLEADO,
        })
        self.assertRedirects(r, reverse('usuarios'))
        self.empleado.refresh_from_db()
        self.assertFalse(self.empleado.is_active)

    def test_no_puede_desactivarse_ni_quitarse_admin_a_si_mismo(self):
        self.client.force_login(self.admin)
        r = self.client.post(reverse('usuario_editar', args=[self.admin.pk]), {
            'first_name': 'Dueño', 'rol': GRUPO_EMPLEADO,
        })
        self.assertEqual(r.status_code, 200)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
        self.assertTrue(self.admin.groups.filter(name=GRUPO_ADMIN).exists())

    def test_otro_admin_puede_degradar_al_dueno(self):
        socio = User.objects.create_user('socio', password=CLAVE, first_name='Socio')
        socio.groups.add(Group.objects.get(name=GRUPO_ADMIN))
        self.client.force_login(socio)
        r = self.client.post(reverse('usuario_editar', args=[self.admin.pk]), {
            'first_name': 'Dueño', 'rol': GRUPO_EMPLEADO, 'is_active': 'on',
        })
        self.assertRedirects(r, reverse('usuarios'))
        self.assertFalse(self.admin.groups.filter(name=GRUPO_ADMIN).exists())

    def test_siempre_queda_un_admin_activo(self):
        from .forms_usuarios import UsuarioEditarForm
        form = UsuarioEditarForm({'first_name': 'Dueño', 'rol': GRUPO_EMPLEADO, 'is_active': 'on'}, instance=self.admin)
        self.assertFalse(form.is_valid())
        self.assertIn('al menos un administrador', str(form.non_field_errors()))
