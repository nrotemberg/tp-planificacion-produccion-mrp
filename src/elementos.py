class ElementoProduccion:
    def __init__(self, nombre, unidad_medida, stock_total, stock_reservado, costo):
        self.nombre = nombre
        self.unidad_medida = unidad_medida
        self.stock_total = stock_total
        self.stock_reservado = stock_reservado
        self.lista_elementos_bom = []
        self.set_costo(costo)

    def set_costo(self, nuevo_costo):
        if not isinstance(nuevo_costo, (int, float)) or nuevo_costo <= 0:
            raise ValueError("El costo debe ser mayor a 0")
        self.costo = nuevo_costo

    def hay_stock_suficiente(self, cantidad_requerida):
        return self.stock_total - self.stock_reservado >= cantidad_requerida

    def construir_bom_manual(self, elemento, cantidad):
        self.agregar_a_BOM(ComponenteBOM(elemento, cantidad))

    def agregar_a_BOM(self, componente):
        if not isinstance(componente, ComponenteBOM):
            raise TypeError("El componente debe ser una instancia de ComponenteBOM")
        self.lista_elementos_bom.append(componente)

    def imprimir_bom(self, nivel=0):
        indentacion = "  " * nivel
        print(f"{indentacion}{self.nombre}")
        for componente in self.lista_elementos_bom:
            elemento = componente.elemento_produccion
            print(f"{indentacion}  ComponenteBOM(nombre='{elemento.nombre}', cantidad={componente.cantidad})")
            if elemento.lista_elementos_bom:
                elemento.imprimir_bom(nivel + 2)

    @staticmethod
    def imprimir_stock(elementos):
        print("\nNombre       | Cantidad | Reservada")
        print("-" * 40)
        for elemento in elementos:
            print(f"{elemento.nombre:12} | {elemento.stock_total:8} | {elemento.stock_reservado:9}")

    def costo_unitario(self):
        return self.costo


class Insumo(ElementoProduccion):
    def get_costo(self):
        return self.costo

    def actualizar_costo(self, nuevo_costo):
        self.set_costo(nuevo_costo)


class ComponenteBOM:
    def __init__(self, elemento_produccion, cantidad):
        self.elemento_produccion = elemento_produccion
        self.validar_cantidad(cantidad)

    def validar_cantidad(self, nueva_cantidad):
        if not isinstance(nueva_cantidad, int) or isinstance(nueva_cantidad, bool) or nueva_cantidad <= 0:
            raise ValueError("La cantidad debe ser un número entero positivo")
        self.cantidad = nueva_cantidad


class Producto(ElementoProduccion):
    def costo_unitario(self):
        costo_total = 0
        for componente in self.lista_elementos_bom:
            costo = componente.elemento_produccion.costo_unitario()
            costo_total += costo * componente.cantidad

        self.costo = costo_total if costo_total > 0 else self.costo
        return self.costo

    def detectar_ciclo(self):
        for componente in self.lista_elementos_bom:
            if self._contiene_elemento(componente.elemento_produccion, set()):
                return True
        return False

    def _contiene_elemento(self, elemento, visitados):
        if elemento is self:
            return True
        if elemento in visitados:
            return False

        visitados.add(elemento)
        for componente in elemento.lista_elementos_bom:
            if self._contiene_elemento(componente.elemento_produccion, visitados):
                return True
        return False