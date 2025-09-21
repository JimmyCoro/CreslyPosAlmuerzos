#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poscresly.settings')
django.setup()

from pedidos.models import Pedido

print("=== CORRECCIÓN DEL ÚLTIMO PEDIDO 'servirse' ===")
print()

# Encontrar el pedido con tipo 'servirse' en minúsculas
pedido_servirse_min = Pedido.objects.filter(tipo='servirse').first()

if pedido_servirse_min:
    print(f"Pedido encontrado:")
    print(f"  - ID: {pedido_servirse_min.id}")
    print(f"  - Tipo actual: '{pedido_servirse_min.tipo}'")
    print(f"  - Fecha: {pedido_servirse_min.fecha_creacion}")
    print()
    
    # Corregir el tipo
    pedido_servirse_min.tipo = 'Servirse'
    pedido_servirse_min.save()
    
    print("✅ Pedido corregido exitosamente")
    print(f"  - Nuevo tipo: '{pedido_servirse_min.tipo}'")
else:
    print("✅ No se encontraron pedidos con tipo 'servirse' en minúsculas")

print()

# Verificar el resultado
pedidos_servirse_min = Pedido.objects.filter(tipo='servirse').count()
pedidos_servirse_may = Pedido.objects.filter(tipo='Servirse').count()

print("Verificación final:")
print(f"  - 'servirse' (min): {pedidos_servirse_min}")
print(f"  - 'Servirse' (may): {pedidos_servirse_may}")
print()

if pedidos_servirse_min == 0:
    print("🎉 ¡Problema completamente solucionado!")
    print("💡 Ahora las tabs deberían funcionar correctamente")
else:
    print("⚠️  Aún hay pedidos con tipos en minúsculas")

print()
print("=== FIN DE CORRECCIÓN ===")
