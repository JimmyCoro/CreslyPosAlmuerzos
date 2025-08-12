# 🍽️ CreslyPos - Sistema de Pedidos para Restaurante

Sistema de punto de venta (POS) desarrollado en Django para gestionar pedidos de restaurante con menú del día, diferentes tipos de pedidos (servirse, llevar, reservado) y control de caja diaria.

## ✨ Características

- 📋 **Gestión de Menú del Día**: Configuración de sopas, segundos y jugos
- 🛒 **Sistema de Pedidos**: Crear y editar pedidos con productos personalizables
- 💰 **Control de Caja**: Seguimiento de ventas por forma de pago
- 📱 **Interfaz Responsiva**: Funciona en desktop y móvil
- 🔄 **Edición de Pedidos**: Modificar cantidades y agregar productos
- 📊 **Resumen de Pedidos**: Vista completa de todos los pedidos pendientes

## 🚀 Instalación

### Requisitos Previos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Git (opcional)

### Pasos de Instalación

1. **Clonar el repositorio**
```bash
git clone https://github.com/JimmyCoro/CreslyPosAlmuerzos.git
cd CreslyPosAlmuerzos/poscresly
```

2. **Crear entorno virtual**
```bash
python -m venv venv
```

3. **Activar entorno virtual**
```bash
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

4. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

5. **Aplicar migraciones**
```bash
python manage.py migrate
```

6. **Crear superusuario (opcional)**
```bash
python manage.py createsuperuser
```

7. **Ejecutar servidor**
```bash
python manage.py runserver
```

8. **Abrir en navegador**
```
http://127.0.0.1:8000/
```

## 📁 Estructura del Proyecto

```
CreslyPos/
├── poscresly/                 # Proyecto Django principal
│   ├── inicio/               # App principal
│   ├── menu/                 # App de gestión de menú
│   ├── pedidos/              # App de gestión de pedidos
│   ├── static/               # Archivos estáticos (CSS, JS, imágenes)
│   ├── templates/            # Plantillas HTML
│   └── manage.py
└── README.md
```

## 🎯 Funcionalidades Principales

### Configuración de Menú
- Configurar sopas, segundos y jugos del día
- Establecer cantidades disponibles
- Gestión de precios por tipo de pedido

### Gestión de Pedidos
- **Crear pedidos**: Almuerzos, sopas, segundos
- **Tipos de pedido**: Servirse, llevar, reservado
- **Formas de pago**: Efectivo, transferencia
- **Edición**: Modificar cantidades y agregar productos
- **Observaciones**: Notas especiales por producto

### Control de Caja
- Seguimiento diario de ventas
- Total por forma de pago
- Historial de pedidos

## 🔧 Configuración

### Variables de Entorno
El proyecto usa configuración por defecto de Django. Para producción, considera configurar:

- `SECRET_KEY`
- `DEBUG = False`
- Base de datos PostgreSQL
- Configuración de archivos estáticos

### Base de Datos
Por defecto usa SQLite. Para producción, se recomienda PostgreSQL:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'creslypos_db',
        'USER': 'tu_usuario',
        'PASSWORD': 'tu_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 🐛 Solución de Problemas

### Error de migraciones
```bash
python manage.py makemigrations
python manage.py migrate
```

### Error de dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Error de archivos estáticos
```bash
python manage.py collectstatic
```

## 📝 Uso del Sistema

1. **Configurar Menú del Día**
   - Ir a "Configurar Menú"
   - Seleccionar sopas, segundos y jugos
   - Establecer cantidades

2. **Crear Pedido**
   - Hacer clic en "¡Haz tu pedido!"
   - Seleccionar tipo de pedido (servirse/llevar/reservado)
   - Agregar productos
   - Confirmar pedido

3. **Editar Pedido**
   - Hacer clic en "Editar" en cualquier pedido
   - Modificar cantidades o agregar productos
   - Guardar cambios

4. **Marcar como Completado**
   - Hacer clic en "Marcar Listo" cuando el pedido esté listo

## 🤝 Contribuir

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 👨‍💻 Autor

**Jimmy Coro**
- GitHub: [@JimmyCoro](https://github.com/JimmyCoro)

## 🙏 Agradecimientos

- Django Framework
- Bootstrap para el diseño
- Font Awesome para los iconos

---

⭐ Si te gusta este proyecto, ¡dale una estrella en GitHub!
