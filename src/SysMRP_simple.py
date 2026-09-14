class SistemaMRP:
    def __init__(self):
        self.elementos_produccion = []
        self.colaboradores = []
        self.unidades_trabajo = []
        self.solicitudes = []

    def agregar_elemento(self, elemento):
        self.elementos_produccion.append(elemento)
        return True

    def crear_solicitud(self, solicitud):
        if self.obtener_solicitud_por_id(solicitud.id) is not None:
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
        if solicitud is None:
            return False
        if not self.verificar_stock(id_solicitud):
            return False
        self._reservar_componentes(solicitud.producto, solicitud.cantidad)
        solicitud.cambiar_estado("planificada")
        return True

    def consumir_stock(self, id_solicitud):
        solicitud = self.obtener_solicitud_por_id(id_solicitud)
        if solicitud is None:
            return False
        self._consumir_componentes(solicitud.producto, solicitud.cantidad)
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
        return self._verificar_componentes(solicitud.producto, solicitud.cantidad)

    def iniciar_produccion(self, id_solicitud):
        solicitud = self.obtener_solicitud_por_id(id_solicitud)
        if solicitud is None or solicitud.estado not in ("planificada", "creada"):
            return False
        solicitud.cambiar_estado("en curso")
        return True

    def finalizar_produccion(self, id_solicitud):
        return self.consumir_stock(id_solicitud)

    def detectar_cuello(self):
        pass

    def _verificar_componentes(self, elemento, cantidad_requerida):
        if not elemento.lista_elementos_bom:
            return elemento.hay_stock_suficiente(cantidad_requerida)

        for componente in elemento.lista_elementos_bom:
            cantidad = componente.cantidad * cantidad_requerida
            if not self._verificar_componentes(componente.elemento_produccion, cantidad):
                return False
        return True

    def _reservar_componentes(self, elemento, cantidad_requerida):
        if not elemento.lista_elementos_bom:
            elemento.stock_reservado += cantidad_requerida
            return

        for componente in elemento.lista_elementos_bom:
            cantidad = componente.cantidad * cantidad_requerida
            self._reservar_componentes(componente.elemento_produccion, cantidad)

    def _consumir_componentes(self, elemento, cantidad_requerida):
        if not elemento.lista_elementos_bom:
            elemento.stock_total -= cantidad_requerida
            elemento.stock_reservado -= cantidad_requerida
            return

        for componente in elemento.lista_elementos_bom:
            cantidad = componente.cantidad * cantidad_requerida
            self._consumir_componentes(componente.elemento_produccion, cantidad)
