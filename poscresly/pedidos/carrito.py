class Carrito:
    """Clase para gestionar el carrito de almuerzos en la sesión del usuario."""
    
    def __init__(self, request):
        self.session = request.session
        carrito = self.session.get('carrito')
        if not carrito:
            carrito = self.session['carrito'] = {}
        self.carrito = carrito

    def agregar(self, tipo_producto, sopa_id=None, segundo_id=None, jugo_id=None, cantidad=1, actualizar=False, observacion=None, precio_unitario=0):
        # Manejar valores None para evitar problemas en la generación de claves
        sopa_id = str(sopa_id) if sopa_id is not None else ''
        segundo_id = str(segundo_id) if segundo_id is not None else ''
        jugo_id = str(jugo_id) if jugo_id is not None else ''
        observacion = str(observacion) if observacion is not None else ''
        
        if tipo_producto == "almuerzo":
            clave = f"A_{sopa_id}_{segundo_id}_{jugo_id}_{observacion}"
        elif tipo_producto == "sopa":
            clave = f"So_{sopa_id}_{jugo_id}_{observacion}"
        elif tipo_producto == "segundo":
            clave = f"Se_{segundo_id}_{jugo_id}_{observacion}"
        else:
            raise ValueError("tipo de producto no válido")

        if clave not in self.carrito:
            self.carrito[clave] = {
                'tipo': tipo_producto,
                'sopa_id': sopa_id if sopa_id else None,
                'segundo_id': segundo_id if segundo_id else None,
                'jugo_id': jugo_id if jugo_id else None,
                'cantidad': 0,
                'observacion': observacion if observacion else None,
                'precio_unitario': precio_unitario
            }

        if actualizar:
            self.carrito[clave]['cantidad'] = cantidad
        else:
            self.carrito[clave]['cantidad'] += cantidad

        self.guardar()

    def guardar(self):
        self.session['carrito'] = self.carrito
        self.session.modified = True

    def eliminar(self, clave):
        if clave in self.carrito:
            del self.carrito[clave]
            self.guardar()

    def limpiar(self):
        self.session['carrito'] = {}
        self.session.modified = True

    def __iter__(self):
        for clave, item in self.carrito.items():
            yield item

    def __len__(self):
        return sum(item['cantidad'] for item in self.carrito.values())

    def get_total_items(self):
        return sum(item['cantidad'] for item in self.carrito.values())

