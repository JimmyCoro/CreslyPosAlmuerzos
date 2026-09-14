import json
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from . import servicio
from .models import MenuDia, MenuDiaJugo, MenuDiaSegundo, MenuDiaSopa, Plato

User = get_user_model()


@override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class MenuDelDiaTests(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.create_superuser('admin', password='x'))
        self.sopas =[Plato.objects.create(nombre_plato=n, tipo='sopa') for n in ('Crema de zapallo', 'Sancocho')]
        self.segundos = [Plato.objects.create(nombre_plato=n, tipo='segundo')
                         for n in ('Pollo al horno', 'Seco de carne', 'Tallarín')]
        self.jugo = Plato.objects.create(nombre_plato='Maracuyá', tipo='jugo')

    def _payload(self, cupo=20):
        return {
            'sopa': [{'plato_id': p.id, 'cupo': cupo} for p in self.sopas],
            'segundo': [{'plato_id': p.id, 'cupo': cupo} for p in self.segundos[:2]],
            'jugo': [{'plato_id': self.jugo.id}],
        }

    def _post(self, name, data):
        return self.client.post(reverse(name), json.dumps(data), content_type='application/json')

    def test_sin_configurar(self):
        r = self.client.get(reverse('menu'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'faltan sopas y segundos')
        self.assertContains(r, 'Configurar el menú')
        self.assertContains(r, 'Sin sopas para hoy')

    def test_tarjeta_bebidas_incluye_agua(self):
        # Sin configurar: el agua ya aparece en su propia tarjeta.
        menu = servicio.construir_menu(servicio.menu_de_hoy())
        bebidas = menu['categorias'][-1]
        self.assertEqual(bebidas['nombre'], 'Bebidas')
        self.assertEqual([r['plato']['nombre'] for r in bebidas['ranuras']], ['Agua'])

        self._post('menu_publicar', self._payload())
        menu = servicio.construir_menu(servicio.menu_de_hoy())
        bebidas = menu['categorias'][-1]
        self.assertEqual([(r['plato']['nombre'], r['siempre']) for r in bebidas['ranuras']],
                         [('Maracuyá', False), ('Agua', True)])
        self.assertEqual(bebidas['meta'], '2 opciones')

        r = self.client.get(reverse('menu'))
        self.assertContains(r, 'BEBIDAS')
        self.assertContains(r, 'DEL DÍA')
        self.assertContains(r, 'SIEMPRE')
        # Republicar sin jugos no borra el agua del menú.
        data = self._payload()
        data['jugo'] = []
        self._post('menu_publicar', data)
        self.assertTrue(MenuDiaJugo.objects.filter(jugo__nombre_plato='Agua').exists())
        self.assertFalse(MenuDiaJugo.objects.filter(jugo=self.jugo).exists())

    def test_frases(self):
        f = servicio.campos_faltantes({'sopa': 0, 'segundo': 1})
        self.assertEqual(servicio.frase_faltantes(f), 'faltan 2 sopas y 1 segundo')
        self.assertEqual(servicio.frase_faltantes(f, contar=False), 'faltan sopas y 1 segundo')
        self.assertEqual(servicio.frase_faltantes(servicio.campos_faltantes({'sopa': 2, 'segundo': 1})), 'falta 1 segundo')
        self.assertEqual(servicio.fecha_corta(date(2026, 9, 12)), 'Sábado 12')

    def test_publicar_incompleto_se_rechaza(self):
        data = self._payload()
        data['segundo'] = data['segundo'][:1]
        r = self._post('menu_publicar', data)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['error'], 'Falta 1 segundo')
        self.assertFalse(MenuDiaSopa.objects.exists())

    def test_publicar_y_leer(self):
        r = self._post('menu_publicar', self._payload())
        self.assertTrue(r.json()['ok'])
        r = self.client.get(reverse('menu'))
        self.assertContains(r, '40 almuerzos disponibles')
        self.assertNotContains(r, 'Configurar el menú')

        parcial = self.client.get(reverse('menu') + '?parcial=1').json()
        self.assertTrue(parcial['publicado'])
        self.assertIn('Sancocho', parcial['secciones'])

    def test_republicar_conserva_vendidos(self):
        self._post('menu_publicar', self._payload(cupo=20))
        item = MenuDiaSopa.objects.get(sopa=self.sopas[0])
        item.cantidad_actual = 15  # 5 vendidas
        item.save()
        self._post('menu_publicar', self._payload(cupo=30))
        item.refresh_from_db()
        self.assertEqual((item.cantidad, item.cantidad_actual), (30, 25))

    def test_semaforo(self):
        self._post('menu_publicar', self._payload(cupo=10))
        MenuDiaSegundo.objects.filter(segundo=self.segundos[0]).update(cantidad_actual=0)
        MenuDiaSegundo.objects.filter(segundo=self.segundos[1]).update(cantidad_actual=3)
        menu = servicio.construir_menu(servicio.menu_de_hoy())
        estados = [r['estado'] for r in menu['categorias'][1]['ranuras']]
        self.assertEqual(estados, ['agotado', 'por_agotarse'])
        self.assertEqual(menu['almuerzos_disponibles'], 3)

    def test_repetidos_y_tipo_incorrecto(self):
        data = self._payload()
        data['sopa'][1]['plato_id'] = self.sopas[0].id
        self.assertEqual(self._post('menu_publicar', data).status_code, 400)
        data = self._payload()
        data['sopa'][1]['plato_id'] = self.segundos[2].id
        self.assertEqual(self._post('menu_publicar', data).status_code, 400)

    def test_configurar_y_copiar_anterior(self):
        ayer = MenuDia.objects.create(fecha=date.today() - timedelta(days=1))
        MenuDiaSopa.objects.create(menu=ayer, sopa=self.sopas[1], cantidad=25)
        r = self.client.get(reverse('menu_configurar') + '?copiar=1')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Copiar ayer')
        estado = r.context['estado']
        self.assertTrue(estado['copiar_al_abrir'])
        sopa = next(p for p in estado['recetario']['sopa'] if p['id'] == self.sopas[1].id)
        self.assertEqual(sopa['veces_mes'] if ayer.fecha.month == date.today().month else 1, 1)
        self.assertEqual(estado['categorias'][0]['pista']['cuando'], 'ayer')

    def test_crear_plato(self):
        r = self._post('menu_crear_plato', {'categoria': 'sopa', 'nombre': '  caldo de   gallina '})
        self.assertEqual(r.json()['plato']['nombre'], 'Caldo de gallina')
        r = self._post('menu_crear_plato', {'categoria': 'sopa', 'nombre': 'CALDO DE GALLINA'})
        self.assertTrue(r.json()['plato']['existia'])
        self.assertEqual(self._post('menu_crear_plato', {'categoria': 'sopa', 'nombre': ''}).status_code, 400)
