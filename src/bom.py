class GestorBOM:
    def explotar(self, elemento, cantidad):
        """Devuelve los insumos necesarios para producir una cantidad."""
        requerimientos = {}
        self._agregar_requerimientos(elemento, cantidad, requerimientos, set())
        return requerimientos

    def _agregar_requerimientos(self, elemento, cantidad, requerimientos, visitados):
        if not elemento.lista_elementos_bom:
            requerimientos[elemento] = requerimientos.get(elemento, 0) + cantidad
            return

        if elemento in visitados:
            raise ValueError("La BOM contiene un ciclo")

        visitados.add(elemento)
        for componente in elemento.lista_elementos_bom:
            cantidad_componente = cantidad * componente.cantidad
            self._agregar_requerimientos(
                componente.elemento_produccion,
                cantidad_componente,
                requerimientos,
                visitados,
            )
        visitados.remove(elemento)
