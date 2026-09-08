# Tu implementacion va aqui
class ElementoProduccion: #Clase base para Insumo y Producto
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

    def hay_stock_suficiente(self, cantidad_requerida): #Metodo para verificar si hay stock suficiente
        disponible = self.stock_total - self.stock_reservado
        return disponible >= cantidad_requerida

    def construir_bom_manual(self, elemento, cantidad):
        self.lista_elementos_bom.append(ComponenteBOM(elemento, cantidad))

    def imprimir_bom(self, nivel=0):
        indentacion = "  " * nivel
        print(f"{indentacion}{self.nombre}")
        for componente in self.lista_elementos_bom:
            elemento = componente.elemento_produccion
            print(
                f"{indentacion}  "
                f"ComponenteBOM(nombre='{elemento.nombre}', "
                f"cantidad={componente.cantidad})"
            )
            if elemento.lista_elementos_bom:
                elemento.imprimir_bom(nivel + 2)

    @staticmethod
    def imprimir_stock(elementos):
        print("\nNombre       | Cantidad | Reservada")
        print("-" * 40)
        for elemento in elementos:
            print(
                f"{elemento.nombre:12} | "
                f"{elemento.stock_total:8} | "
                f"{elemento.stock_reservado:9}"
            )

    def costo_unitario(self): #Metodo para obtener el costo unitario del elemento de producción
        pass


class Insumo(ElementoProduccion): #Subclase de ElementoProduccion, representa un insumo que se utiliza en la producción de un producto
    def __init__(self, nombre, unidad_medida, stock_total, stock_reservado, costo):
        super().__init__(nombre, unidad_medida, stock_total, stock_reservado, costo)

    def get_costo(self): #Metodo para obtener el costo del insumo
        return self.costo

    def set_costo(self, nuevo_costo): #Metodo para actualizar el costo del insumo
        if not isinstance(nuevo_costo, (int, float)) or nuevo_costo <= 0:
            raise ValueError("El costo debe ser mayor a 0")
        self.costo = nuevo_costo

    def actualizar_costo(self, nuevo_costo):
        self.set_costo(nuevo_costo)


class ComponenteBOM: #Clase que representa un componente de la lista de materiales (BOM) de un producto
    def __init__(self, elemento_produccion, cantidad):
        self.elemento_produccion = elemento_produccion
        self.set_cantidad(cantidad) #Se utiliza el metodo set_cantidad para validar la cantidad del componente

    def set_cantidad(self, nueva_cantidad): #Metodo para validar que la cantidad del componente sea entera y positiva
        if isinstance(nueva_cantidad, int) and nueva_cantidad > 0:
            self.cantidad = nueva_cantidad
        else:
            raise ValueError("La cantidad debe ser un número entero positivo")
        pass


class Producto(ElementoProduccion): #Subclase de ElementoProduccion, representa un producto que se produce a partir de insumos y componentes
    def __init__(self, nombre, unidad_medida, stock_total, stock_reservado, costo):
            super().__init__(nombre, unidad_medida, stock_total, stock_reservado, costo)

    def costo_unitario(self): #Metodo para obtener el costo del producto
        costo_total = 0

        for componente in self.lista_elementos_bom:
            elemento = componente.elemento_produccion
            cantidad = componente.cantidad

            if isinstance(elemento, Insumo):
                costo_total += elemento.get_costo() * cantidad
            elif isinstance(elemento, Producto):
                costo_total += elemento.costo_unitario() * cantidad
        self.costo = costo_total

        return costo_total


class ProcesoManufactura:
    pass


class TareaDefinida:
    pass


class TareaEnCurso:
    pass


class UnidadTrabajo:
    pass


class Colaborador:
    pass


class PeriodoOperacion:
    pass


class Solicitud: #Clase que representa una solicitud de producción de un producto
    def __init__(self, id, producto, cantidad):
        self.id = id
        self.producto = producto
        self.cantidad = cantidad

    def _verificar_componentes(self, elemento, cantidad_requerida):
        """Recursivamente verifica stock de componentes"""
        if not elemento.lista_elementos_bom:
            return elemento.hay_stock_suficiente(cantidad_requerida)

        for componente in elemento.lista_elementos_bom:
            elem = componente.elemento_produccion
            cant = componente.cantidad * cantidad_requerida
            if not self._verificar_componentes(elem, cant):
                return False
        return True
    
    def verificar_stock(self): #Metodo para verificar si hay stock suficiente de los elementos de producción necesarios para la solicitud
        return self._verificar_componentes(self.producto, self.cantidad)

    def _reservar_componentes(self, elemento, cantidad_requerida):
        """Recursivamente reserva componentes"""
        if not elemento.lista_elementos_bom:
            elemento.stock_reservado += cantidad_requerida
            return

        for componente in elemento.lista_elementos_bom:
            elem = componente.elemento_produccion
            cant = componente.cantidad * cantidad_requerida
            self._reservar_componentes(elem, cant)
    
    def reservar(self): #Metodo para reservar recursos para la solicitud
        if not self.verificar_stock():
            return False
        self._reservar_componentes(self.producto, self.cantidad)
        return True

    def _consumir_componentes(self, elemento, cantidad_requerida):
        """Recursivamente consume stock de componentes"""
        if not elemento.lista_elementos_bom:
            elemento.stock_total -= cantidad_requerida
            elemento.stock_reservado -= cantidad_requerida
            return

        for componente in elemento.lista_elementos_bom:
            elem = componente.elemento_produccion
            cant = componente.cantidad * cantidad_requerida
            self._consumir_componentes(elem, cant)
    
    def consumir_stock(self): #Metodo para consumir el stock del producto solicitado
        self._consumir_componentes(self.producto, self.cantidad)
        self.producto.stock_total += self.cantidad
        return True

