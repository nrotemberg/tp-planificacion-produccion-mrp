from src.bom import GestorBOM
from src.inventario import Inventario


class SistemaMRP:
    def __init__(self):
        self.elementos_produccion = {}
        self.colaboradores = []
        self.unidades_trabajo = []
        self.solicitudes = {}
        self.inventario = Inventario()
        self.bom = GestorBOM()
        self.planes_materiales = {}

    def agregar_elemento(self, elemento):
        if elemento.nombre in self.elementos_produccion:
            return False
        self.elementos_produccion[elemento.nombre] = elemento
        return True

    def crear_solicitud(self, solicitud):
        if self.obtener_solicitud_por_id(solicitud.id) is not None:
            return False
        self.solicitudes[solicitud.id] = solicitud
        return True

    def obtener_solicitud_por_id(self, id_solicitud):
        return self.solicitudes.get(id_solicitud)

    def reservar_recursos(self, id_solicitud):
        """Reserva insumos faltantes y subproductos existentes."""
        solicitud = self.obtener_solicitud_por_id(id_solicitud)
        if solicitud is None or solicitud.estado != "creada":
            return False

        requerimientos, consumos_stock = self._obtener_plan_materiales(solicitud)
        if not self.inventario.hay_stock(requerimientos):
            return False
        if not self.inventario.hay_stock(consumos_stock):
            return False

        self.inventario.reservar(requerimientos)
        self.inventario.reservar(consumos_stock)
        self.planes_materiales[solicitud.id] = (requerimientos, consumos_stock)
        solicitud.cambiar_estado("planificada")
        return True

    def consumir_stock(self, id_solicitud):
        solicitud = self.obtener_solicitud_por_id(id_solicitud)
        if solicitud is None or solicitud.estado != "en curso":
            return False

        requerimientos, consumos_stock = self.planes_materiales.get(
            solicitud.id,
            self._obtener_plan_materiales(solicitud),
        )
        self.inventario.consumir(requerimientos)
        self.inventario.consumir(consumos_stock)
        solicitud.producto.stock_total += solicitud.cantidad
        solicitud.cambiar_estado("finalizada")
        self.planes_materiales.pop(solicitud.id, None)
        return True

    def agregar_colaborador(self, colaborador):
        pass

    def agregar_unidad_trabajo(self, unidad_trabajo):
        pass

    def planificar_solicitud(self, id_solicitud):
        return self.reservar_recursos(id_solicitud)

    def verificar_stock(self, id_solicitud):
        solicitud = self.obtener_solicitud_por_id(id_solicitud)
        if solicitud is None:
            return False
        requerimientos, consumos_stock = self._obtener_plan_materiales(solicitud)
        return self.inventario.hay_stock(requerimientos) and self.inventario.hay_stock(
            consumos_stock
        )

    def iniciar_produccion(self, id_solicitud):
        solicitud = self.obtener_solicitud_por_id(id_solicitud)
        if solicitud is None or solicitud.estado != "planificada":
            return False
        solicitud.cambiar_estado("en curso")
        return True

    def finalizar_produccion(self, id_solicitud):
        return self.consumir_stock(id_solicitud)

    def detectar_cuello(self):
        pass

    def _obtener_requerimientos(self, solicitud):
        requerimientos, _ = self._obtener_plan_materiales(solicitud)
        return requerimientos

    def _obtener_plan_materiales(self, solicitud):
        """Separa lo que hay que fabricar de lo que ya existe en stock.

        `requerimientos` contiene los insumos faltantes que `hay_stock`
        verifica para fabricar. `consumos_stock` contiene los subproductos
        que ya estaban disponibles y que también deben reservarse para no
        asignarlos a otra solicitud.
        """
        consumos_stock = {}
        return self.bom.explotar(
            solicitud.producto,
            solicitud.cantidad,
            self.inventario,
            consumos_stock,
        ), consumos_stock
