import math

from src.excepciones import (
    BOMCiclicaError,
    CantidadInvalidaError,
    CostoInvalidoError,
    TipoInvalidoError,
)


class ElementoProduccion:
    def __init__(self, nombre, unidad_medida, costo):
        self._validar_texto(nombre, "El nombre")
        self._validar_texto(unidad_medida, "La unidad de medida")
        self.nombre = nombre
        self.unidad_medida = unidad_medida
        self._lista_elementos_bom = []
        self.set_costo(costo)

    @property
    def lista_elementos_bom(self):
        if "_lista_elementos_bom" not in self.__dict__:
            componentes = self.__dict__.pop("lista_elementos_bom", [])
            self._lista_elementos_bom = componentes
        return tuple(self._lista_elementos_bom)

    @staticmethod
    def _validar_texto(valor, campo):
        if not isinstance(valor, str) or not valor.strip():
            raise TipoInvalidoError(f"{campo} debe ser un texto no vacío")

    def set_costo(self, nuevo_costo):
        es_numero = isinstance(nuevo_costo, (int, float)) and not isinstance(
            nuevo_costo, bool
        )
        es_finito = not isinstance(nuevo_costo, float) or math.isfinite(nuevo_costo)
        if not es_numero or not es_finito or nuevo_costo <= 0:
            raise CostoInvalidoError("El costo debe ser un número finito mayor a 0")
        self.costo = nuevo_costo

    def construir_bom_manual(self, elemento, cantidad):
        self.agregar_a_BOM(ComponenteBOM(elemento, cantidad))

    def agregar_a_BOM(self, componente):
        if not isinstance(componente, ComponenteBOM):
            raise TipoInvalidoError("El componente debe ser una instancia de ComponenteBOM")
        elemento = componente.elemento_produccion
        if (
            self.detectar_ciclo()
            or elemento.detectar_ciclo()
            or self._alcanza(elemento, self, set())
        ):
            raise BOMCiclicaError("La BOM contiene un ciclo")
        self._lista_elementos_bom.append(componente)

    def imprimir_bom(self, nivel=0):
        if self.detectar_ciclo():
            raise BOMCiclicaError("La BOM contiene un ciclo")

        indentacion = "  " * nivel
        print(f"{indentacion}{self.nombre}")
        for componente in self.lista_elementos_bom:
            elemento = componente.elemento_produccion
            print(f"{indentacion}  ComponenteBOM(nombre='{elemento.nombre}', cantidad={componente.cantidad})")
            if elemento.lista_elementos_bom:
                elemento.imprimir_bom(nivel + 2)

    @staticmethod
    def _alcanza(elemento, objetivo, visitados):
        if elemento is objetivo:
            return True
        if elemento in visitados:
            return False

        visitados.add(elemento)
        return any(
            ElementoProduccion._alcanza(
                componente.elemento_produccion, objetivo, visitados
            )
            for componente in elemento.lista_elementos_bom
        )

    @staticmethod
    def _tiene_ciclo(elemento, en_recorrido, visitados):
        if elemento in en_recorrido:
            return True
        if elemento in visitados:
            return False

        en_recorrido.add(elemento)
        for componente in elemento.lista_elementos_bom:
            if ElementoProduccion._tiene_ciclo(
                componente.elemento_produccion, en_recorrido, visitados
            ):
                return True
        en_recorrido.remove(elemento)
        visitados.add(elemento)
        return False

    def detectar_ciclo(self):
        return self._tiene_ciclo(self, set(), set())

    def costo_unitario(self):
        return self.costo


class Insumo(ElementoProduccion):
    def get_costo(self):
        return self.costo

    def actualizar_costo(self, nuevo_costo):
        self.set_costo(nuevo_costo)


class ComponenteBOM:
    def __init__(self, elemento_produccion, cantidad):
        if not isinstance(elemento_produccion, ElementoProduccion):
            raise TipoInvalidoError(
                "El elemento debe ser una instancia de ElementoProduccion"
            )
        self.elemento_produccion = elemento_produccion
        self.validar_cantidad(cantidad)

    def validar_cantidad(self, nueva_cantidad):
        if (
            not isinstance(nueva_cantidad, int)
            or isinstance(nueva_cantidad, bool)
            or nueva_cantidad <= 0
        ):
            raise CantidadInvalidaError("La cantidad debe ser un número entero positivo")
        self.cantidad = nueva_cantidad


class Producto(ElementoProduccion):
    def __init__(self, nombre, unidad_medida, costo):
        super().__init__(nombre, unidad_medida, costo)
        self.proceso_manufactura = None

    def costo_unitario(self):
        if self.detectar_ciclo():
            raise BOMCiclicaError("La BOM contiene un ciclo")

        costo_materiales = 0
        for componente in self.lista_elementos_bom:
            costo = componente.elemento_produccion.costo_unitario()
            costo_materiales += costo * componente.cantidad

        costo_manufactura = 0
        proceso = getattr(self, "proceso_manufactura", None)
        if proceso is not None:
            costo_manufactura = (
                proceso.calcular_costo_operativo()
            )

        costo_total = costo_materiales + costo_manufactura
        if costo_total > 0:
            self.costo = costo_total
        return self.costo