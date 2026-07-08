import json
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError

from pizzeria.models import (
    ComboComponente,
    ComboPizzeria,
    ComboTamano,
    ProductoSimple,
    Sabor,
    TamanoPizza,
)

DEFAULT_PATH = r"C:\Users\Jimmy\Desktop\PROYECTOS REALES\MenuDigital\cresly_pizzeria\datos.json"

CATEGORIA_PIZZAS = 1
CATEGORIA_ALITAS = 2
CATEGORIA_BEBIDAS = 4
CATEGORIA_PARA_PICAR = 6
CATEGORIA_MEGA_COMBOS = 7
CATEGORIA_HAMBURGUESAS = 8
CATEGORIA_COMPARTIR = 9
CATEGORIA_COMBOS_INSTANTE = 10

CATEGORIA_A_PRODUCTOSIMPLE = {
    CATEGORIA_ALITAS: 'alitas',
    CATEGORIA_BEBIDAS: 'bebida',
    CATEGORIA_PARA_PICAR: 'para_picar',
    CATEGORIA_HAMBURGUESAS: 'hamburguesa',
    CATEGORIA_COMPARTIR: 'otro',
    CATEGORIA_COMBOS_INSTANTE: 'otro',
}

# Recargos premium confirmados por el dueño del negocio (no vienen en el dato de origen)
RECARGOS_PREMIUM = {
    'Pequeña': {'completo': Decimal('0.75'), 'mitad': Decimal('0.40')},
    'Mediana': {'completo': Decimal('1.00'), 'mitad': Decimal('0.50')},
    'Familiar': {'completo': Decimal('1.50'), 'mitad': Decimal('0.75')},
}
ORDEN_TAMANOS = {'Pequeña': 1, 'Mediana': 2, 'Familiar': 3}

# Composición estructurada de cada Mega Combo (misma para sus 3 tamaños)
COMBO_COMPONENTES = {
    'Mega Combo 1': [
        ('papas', 1, ''),
        ('alitas', 6, ''),
        ('bebida', 1, ''),
        ('postre', 1, 'Fresas con crema'),
    ],
    'Mega Combo 2': [
        ('papas', 1, ''),
        ('bebida', 1, ''),
        ('postre', 1, 'Fresas con crema'),
        ('helado', 1, ''),
    ],
    'Mega Combo 3': [
        ('papas', 1, ''),
        ('alitas', 10, ''),
        ('bebida', 1, ''),
        ('postre', 1, 'Fresas con crema'),
    ],
    'Mega Combo 4': [
        ('papas', 1, ''),
        ('alitas', 6, ''),
        ('bebida', 1, ''),
        ('postre', 1, 'Fresas con crema'),
        ('helado', 1, ''),
    ],
}


class Command(BaseCommand):
    help = 'Importa el catálogo real (sabores, tamaños, combos, productos) desde el datos.json de MenuDigital'

    def add_arguments(self, parser):
        parser.add_argument('--path', default=DEFAULT_PATH, help='Ruta al datos.json de MenuDigital')

    def handle(self, *args, **options):
        path = options['path']
        try:
            with open(path, encoding='utf-8') as f:
                registros = json.load(f)
        except OSError as exc:
            raise CommandError(f"No se pudo leer '{path}': {exc}")

        productos = [r for r in registros if r['model'] == 'menu.product']
        flavors = [r for r in registros if r['model'] == 'menu.flavor']

        n_sabores = self._importar_sabores(flavors)
        n_tamanos = self._importar_tamanos(productos)
        n_combos, n_combo_tamanos, n_componentes = self._importar_combos(productos)
        n_productos_simples = self._importar_productos_simples(productos)

        self.stdout.write(self.style.SUCCESS(
            f"Importación completa: {n_sabores} sabores, {n_tamanos} tamaños de pizza, "
            f"{n_combos} combos ({n_combo_tamanos} tamaños de combo, {n_componentes} componentes), "
            f"{n_productos_simples} productos simples."
        ))

    def _importar_sabores(self, flavors):
        count = 0
        for r in flavors:
            fields = r['fields']
            tipo = 'pizza' if fields['flavor_type'] == 'PIZZA' else 'alitas'
            Sabor.objects.update_or_create(
                nombre=fields['name'],
                tipo=tipo,
                defaults={
                    'es_premium': fields['is_premium'],
                    'descripcion': fields.get('description', ''),
                },
            )
            count += 1
        return count

    def _importar_tamanos(self, productos):
        count = 0
        for r in productos:
            fields = r['fields']
            if fields['category'] != CATEGORIA_PIZZAS:
                continue
            if not fields['name'].startswith('Pizza '):
                continue  # ej. "Porción individual" no es un tamaño
            nombre = fields['name'].replace('Pizza ', '').strip()
            recargos = RECARGOS_PREMIUM.get(nombre, {'completo': Decimal('0'), 'mitad': Decimal('0')})
            TamanoPizza.objects.update_or_create(
                nombre=nombre,
                defaults={
                    'precio_base': Decimal(fields['price']),
                    'recargo_premium_completo': recargos['completo'],
                    'recargo_premium_mitad': recargos['mitad'],
                    'orden': ORDEN_TAMANOS.get(nombre, 99),
                },
            )
            count += 1
        return count

    def _importar_combos(self, productos):
        combos_productos = [r for r in productos if r['fields']['category'] == CATEGORIA_MEGA_COMBOS]
        n_combos = 0
        n_combo_tamanos = 0
        n_componentes = 0

        grupos = {}
        for r in combos_productos:
            grupos.setdefault(r['fields']['group'], []).append(r['fields'])

        for nombre_combo, filas in grupos.items():
            combo, _ = ComboPizzeria.objects.update_or_create(
                nombre=nombre_combo,
                defaults={'descripcion': filas[0].get('description', ''), 'activo': True},
            )
            n_combos += 1

            for fila in filas:
                try:
                    tamano = TamanoPizza.objects.get(nombre=fila['name'])
                except TamanoPizza.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f"Tamaño '{fila['name']}' no existe, se omite fila de {nombre_combo}"
                    ))
                    continue
                ComboTamano.objects.update_or_create(
                    combo=combo, tamano=tamano, defaults={'precio': Decimal(fila['price'])}
                )
                n_combo_tamanos += 1

            for tipo, cantidad, detalle in COMBO_COMPONENTES.get(nombre_combo, []):
                ComboComponente.objects.update_or_create(
                    combo=combo, tipo=tipo,
                    defaults={'cantidad': cantidad, 'detalle': detalle},
                )
                n_componentes += 1

        return n_combos, n_combo_tamanos, n_componentes

    def _importar_productos_simples(self, productos):
        count = 0
        for r in productos:
            fields = r['fields']
            categoria_origen = fields['category']

            if categoria_origen == CATEGORIA_MEGA_COMBOS:
                continue  # ya procesados como ComboPizzeria

            if categoria_origen == CATEGORIA_PIZZAS:
                if fields['name'].startswith('Pizza '):
                    continue  # ya procesado como TamanoPizza
                categoria = 'otro'  # ej. "Porción individual"
            else:
                categoria = CATEGORIA_A_PRODUCTOSIMPLE.get(categoria_origen, 'otro')

            ProductoSimple.objects.update_or_create(
                nombre=fields['name'],
                categoria=categoria,
                defaults={
                    'descripcion': fields.get('description', ''),
                    'precio': Decimal(fields['price']),
                    'activo': True,
                },
            )
            count += 1
        return count
