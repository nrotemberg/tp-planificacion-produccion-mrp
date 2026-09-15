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
        solicitud = self.obtener_solicitud_por_id(id_solicitud)
        if solicitud is None or solicitud.estado != "creada":
            return False

        requerimientos = self._obtener_requerimientos(solicitud)
        if not self.inventario.hay_stock(requerimientos):
            return False

        self.inventario.reservar(requerimientos)
        solicitud.cambiar_estado("planificada")
        return True

    def consumir_stock(self, id_solicitud):
        solicitud = self.obtener_solicitud_por_id(id_solicitud)
        if solicitud is None or solicitud.estado != "en curso":
            return False

        requerimientos = self._obtener_requerimientos(solicitud)
        self.inventario.consumir(requerimientos)
        solicitud.producto.stock_total += solicitud.cantidad
        solicitud.cambiar_estado("finalizada")
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
        requerimientos = self._obtener_requerimientos(solicitud)
        return self.inventario.hay_stock(requerimientos)

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
        return self.bom.explotar(solicitud.producto, solicitud.cantidad)
