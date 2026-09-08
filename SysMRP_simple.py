class SysMRP:
    def __init__(self):
        self.elementos_produccion = []
        self.solicitudes = []

    def agregar_elemento(self, elemento):
        if self.obtener_elemento_por_nombre(elemento.nombre) is not None:
            return False
        self.elementos_produccion.append(elemento)
        return True

    def obtener_elemento_por_nombre(self, nombre):
        for elemento in self.elementos_produccion:
            if elemento.nombre == nombre:
                return elemento
        return None

    def crear_solicitud(self, solicitud):
        if self.obtener_elemento_por_nombre(solicitud.producto.nombre) is None:
            return False
        self.solicitudes.append(solicitud)
        return True

    def obtener_solicitud_por_id(self, id_solicitud):
        for solicitud in self.solicitudes:
            if solicitud.id == id_solicitud:
                return solicitud
        return None

    def reservar_recursos(self, id_solicitud):
        solicitud = self.obtener_solicitud_por_id(id_solicitud)
        return solicitud is not None and solicitud.reservar()

    def consumir_stock(self, id_solicitud):
        solicitud = self.obtener_solicitud_por_id(id_solicitud)
        return solicitud is not None and solicitud.consumir_stock()
