from src.excepciones import BOMCiclicaError, CantidadInvalidaError


class GestorBOM:
    """Recorre la BOM de un elemento para calcular materiales o mostrarla."""

    @staticmethod
    def validar_agregado(elemento, componente):
        """Rechaza componentes que vuelvan cíclica la BOM de `elemento`."""
        subelemento = componente.elemento_produccion
        GestorBOM.validar_sin_ciclos(elemento)
        GestorBOM.validar_sin_ciclos(subelemento)
        if GestorBOM._alcanza(subelemento, elemento, set()):
            raise BOMCiclicaError("La BOM contiene un ciclo")

    @staticmethod
    def validar_sin_ciclos(elemento):
        """Lanza BOMCiclicaError si el elemento tiene una BOM cíclica."""
        if GestorBOM.detectar_ciclo(elemento):
            raise BOMCiclicaError("La BOM contiene un ciclo")

    @staticmethod
    def detectar_ciclo(elemento):
        """Indica si la BOM contiene un ciclo directo o indirecto."""
        return GestorBOM._tiene_ciclo(elemento, set(), set())

    @staticmethod
    def _alcanza(elemento, objetivo, visitados):
        if elemento is objetivo:
            return True
        if elemento in visitados:
            return False

        visitados.add(elemento)
        return any(
            GestorBOM._alcanza(
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
            if GestorBOM._tiene_ciclo(
                componente.elemento_produccion, en_recorrido, visitados
            ):
                return True
        en_recorrido.remove(elemento)
        visitados.add(elemento)
        return False

    @staticmethod
    def _validar_cantidad(cantidad):
        if not isinstance(cantidad, int) or isinstance(cantidad, bool) or cantidad <= 0:
            raise CantidadInvalidaError(
                "La cantidad debe ser un número entero positivo"
            )

    def calcular_requerimientos(
        self, elemento, cantidad, descontar_stock=False, inventario=None
    ):
        """Devuelve (faltantes, disponibles) para fabricar `cantidad`.

        `faltantes` son los insumos que hay que conseguir. `disponibles` son
        los subproductos que ya estaban en stock y que igual hay que reservar
        para no asignarlos a otra solicitud.

        Con `descontar_stock=False` el resultado es la BOM completa, sin mirar
        el stock.
        """
        self._validar_cantidad(cantidad)
        if descontar_stock and inventario is None:
            raise ValueError("Se necesita un inventario para descontar stock")

        self.faltantes = {}
        self.disponibles = {}
        self.stock_libre = {}
        self.visitados = set()
        self.descontar_stock = descontar_stock
        self.inventario = inventario

        self._recorrer(elemento, cantidad)
        return self.faltantes, self.disponibles

    def _stock_libre(self, nodo):
        if self.inventario is None:
            return 0
        try:
            return max(self.inventario.stock_libre(nodo), 0)
        except KeyError:
            return 0

    def _recorrer(self, nodo, necesidad):
        """Suma a self.faltantes y self.disponibles lo que pide `nodo`.

        `necesidad` es cuantas unidades de `nodo` hacen falta. Si el nodo es un
        subproducto con stock, esa parte no se fabrica y no se piden sus
        componentes.
        """
        if self.descontar_stock and nodo.lista_elementos_bom:
            libre = self.stock_libre.get(nodo)
            if libre is None:
                libre = self._stock_libre(nodo)
            usado = min(necesidad, libre)
            self.stock_libre[nodo] = libre - usado
            if usado:
                self.disponibles[nodo] = self.disponibles.get(nodo, 0) + usado
            necesidad -= usado

        if necesidad == 0:
            return

        # Los elementos sin BOM son los insumos que Inventario debe verificar,
        # reservar y consumir.
        if not nodo.lista_elementos_bom:
            self.faltantes[nodo] = self.faltantes.get(nodo, 0) + necesidad
            return

        if nodo in self.visitados:
            raise BOMCiclicaError("La BOM contiene un ciclo")

        self.visitados.add(nodo)
        try:
            for componente in nodo.lista_elementos_bom:
                self._recorrer(
                    componente.elemento_produccion,
                    necesidad * componente.cantidad,
                )
        finally:
            self.visitados.discard(nodo)

    def arbol_texto(self, elemento, cantidad=1):
        """Devuelve la BOM completa como un arbol de texto.

        Muestra la estructura original de la BOM y no consulta el inventario.
        Por eso aparecen todos los subproductos e insumos, aunque algunos ya
        esten disponibles en stock.
        """
        self._validar_cantidad(cantidad)
        self.lineas = [f"{elemento.nombre} x {cantidad}"]
        self.visitados = set()
        try:
            self._agregar_lineas(elemento, cantidad, "")
        finally:
            self.visitados.clear()
        return "\n".join(self.lineas)

    def _agregar_lineas(self, nodo, necesidad, prefijo):
        """Agrega a self.lineas el subarbol de `nodo` con el `prefijo` dado."""
        if nodo in self.visitados:
            raise BOMCiclicaError("La BOM contiene un ciclo")

        self.visitados.add(nodo)
        try:
            componentes = nodo.lista_elementos_bom
            for indice, componente in enumerate(componentes):
                es_ultimo = indice == len(componentes) - 1
                conector = "`-- " if es_ultimo else "+-- "
                cantidad_componente = necesidad * componente.cantidad
                self.lineas.append(
                    f"{prefijo}{conector}"
                    f"{componente.elemento_produccion.nombre} x {cantidad_componente}"
                )
                nuevo_prefijo = prefijo + ("    " if es_ultimo else "|   ")
                self._agregar_lineas(
                    componente.elemento_produccion,
                    cantidad_componente,
                    nuevo_prefijo,
                )
        finally:
            self.visitados.discard(nodo)
