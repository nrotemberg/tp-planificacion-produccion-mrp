from src.excepciones import BOMCiclicaError


class GestorBOM:
    """Recorre la BOM de un elemento para calcular materiales o mostrarla."""

    def calcular_requerimientos(self, elemento, cantidad, descontar_stock=False):
        """Devuelve (faltantes, disponibles) para fabricar `cantidad`.

        `faltantes` son los insumos que hay que conseguir. `disponibles` son
        los subproductos que ya estaban en stock y que igual hay que reservar
        para no asignarlos a otra solicitud.

        Con `descontar_stock=False` el resultado es la BOM completa, sin mirar
        el stock.
        """
        self.faltantes = {}
        self.disponibles = {}
        self.stock_libre = {}
        self.visitados = set()
        self.descontar_stock = descontar_stock

        self._recorrer(elemento, cantidad)
        return self.faltantes, self.disponibles

    def _recorrer(self, nodo, necesidad):
        """Suma a self.faltantes y self.disponibles lo que pide `nodo`.

        `necesidad` es cuantas unidades de `nodo` hacen falta. Si el nodo es un
        subproducto con stock, esa parte no se fabrica y no se piden sus
        componentes.
        """
        if self.descontar_stock and nodo.lista_elementos_bom:
            libre = self.stock_libre.get(nodo)
            if libre is None:
                libre = max(nodo.stock_total - nodo.stock_reservado, 0)
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
        for componente in nodo.lista_elementos_bom:
            self._recorrer(
                componente.elemento_produccion,
                necesidad * componente.cantidad,
            )
        self.visitados.remove(nodo)

    def arbol_texto(self, elemento, cantidad=1):
        """Devuelve la BOM completa como un arbol de texto.

        Muestra la estructura original de la BOM y no consulta el inventario.
        Por eso aparecen todos los subproductos e insumos, aunque algunos ya
        esten disponibles en stock.
        """
        self.lineas = [f"{elemento.nombre} x {cantidad}"]
        self.visitados = set()
        self._agregar_lineas(elemento, cantidad, "")
        return "\n".join(self.lineas)

    def _agregar_lineas(self, nodo, necesidad, prefijo):
        """Agrega a self.lineas el subarbol de `nodo` con el `prefijo` dado."""
        if nodo in self.visitados:
            raise BOMCiclicaError("La BOM contiene un ciclo")

        self.visitados.add(nodo)
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
        self.visitados.remove(nodo)
