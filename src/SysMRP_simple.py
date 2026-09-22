from src.bom import GestorBOM
from src.inventario import Inventario
from src.solicitudes import Solicitud


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

    def crear_orden_fabricacion(self, id, articulo, cantidad, **parametros):
        solicitante = parametros.pop("solicitante", None)
        solicitud = Solicitud(id, solicitante, "creada", articulo, cantidad, **parametros)
        return self.crear_solicitud(solicitud)

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

        faltantes, disponibles = self._obtener_plan_materiales(solicitud)
        if not self.inventario.hay_stock(faltantes):
            return False
        if not self.inventario.hay_stock(disponibles):
            return False

        self.inventario.reservar(faltantes)
        self.inventario.reservar(disponibles)
        self.planes_materiales[solicitud.id] = (faltantes, disponibles)
        solicitud.cambiar_estado()
        return True

    def consumir_stock(self, id_solicitud):
        solicitud = self.obtener_solicitud_por_id(id_solicitud)
        if solicitud is None or solicitud.estado != "en curso":
            return False

        faltantes, disponibles = self.planes_materiales.get(
            solicitud.id,
            self._obtener_plan_materiales(solicitud),
        )
        self.inventario.consumir(faltantes)
        self.inventario.consumir(disponibles)
        solicitud.producto.stock_total += solicitud.cantidad
        solicitud.cambiar_estado()
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
        faltantes, disponibles = self._obtener_plan_materiales(solicitud)
        return self.inventario.hay_stock(faltantes) and self.inventario.hay_stock(
            disponibles
        )

    def iniciar_produccion(self, id_solicitud):
        solicitud = self.obtener_solicitud_por_id(id_solicitud)
        if solicitud is None or solicitud.estado != "planificada":
            return False
        solicitud.cambiar_estado()
        return True

    def finalizar_produccion(self, id_solicitud):
        return self.consumir_stock(id_solicitud)

    def detectar_cuello(self):
        pass

    def _obtener_plan_materiales(self, solicitud):
        """Separa lo que hay que fabricar de lo que ya existe en stock.

        `faltantes` contiene los insumos que `hay_stock` verifica para
        fabricar. `disponibles` contiene los subproductos que ya estaban en
        stock y que tambien deben reservarse para no asignarlos a otra
        solicitud.
        """
        return self.bom.calcular_requerimientos(
            solicitud.producto,
            solicitud.cantidad,
            descontar_stock=True,
        )
