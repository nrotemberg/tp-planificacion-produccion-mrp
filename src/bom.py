class GestorBOM:
    def formatear_bom(self, elemento, cantidad=1):
        """Devuelve la BOM completa como un arbol de texto.

        Este metodo representa la estructura original de la BOM y no
        consulta el inventario. Por eso muestra todos los subproductos e
        insumos, aunque algunos ya esten disponibles en stock.
        """
        lineas = [f"{elemento.nombre} x {cantidad}"]
        self._agregar_lineas_bom(elemento, cantidad, lineas, "", set())
        return "\n".join(lineas)

    def mostrar_bom(self, elemento, cantidad=1):
        """Muestra en la terminal la BOM completa del elemento."""
        print(self.formatear_bom(elemento, cantidad))

    def formatear_bom_con_insumos(self, elemento, cantidad=1):
        """Devuelve el arbol BOM seguido por una tabla de insumos agregados."""
        arbol = self.formatear_bom(elemento, cantidad)
        tabla = self.formatear_tabla_insumos(elemento, cantidad)
        return f"{arbol}\n\n{tabla}"

    def mostrar_bom_con_insumos(self, elemento, cantidad=1):
        """Muestra el arbol BOM y debajo la tabla de insumos."""
        print(self.formatear_bom_con_insumos(elemento, cantidad))

    def formatear_tabla_insumos(self, elemento, cantidad=1):
        """Devuelve una tabla con cada insumo y su cantidad total."""
        insumos = {}
        self._acumular_insumos(elemento, cantidad, insumos, set())

        nombre_ancho = max(
            len("Insumo"),
            *(len(insumo.nombre) for insumo in insumos),
        )
        cantidad_ancho = max(
            len("Cantidad"),
            *(len(str(cantidad_insumo)) for cantidad_insumo in insumos.values()),
        )
        separador = f"+-{'-' * (nombre_ancho + 2)}-+-{'-' * (cantidad_ancho + 2)}-+"
        lineas = [
            "Insumos totales",
            separador,
            f"| {'Insumo':<{nombre_ancho}} | {'Cantidad':>{cantidad_ancho}} |",
            separador,
        ]
        for insumo in sorted(insumos, key=lambda elemento: elemento.nombre):
            lineas.append(
                f"| {insumo.nombre:<{nombre_ancho}} | "
                f"{insumos[insumo]:>{cantidad_ancho}} |"
            )
        lineas.append(separador)
        return "\n".join(lineas)

    def _acumular_insumos(self, elemento, cantidad, insumos, visitados):
        """Suma las hojas de la BOM sin modificar su estructura."""
        if elemento in visitados:
            raise ValueError("La BOM contiene un ciclo")
        if not elemento.lista_elementos_bom:
            insumos[elemento] = insumos.get(elemento, 0) + cantidad
            return

        visitados.add(elemento)
        for componente in elemento.lista_elementos_bom:
            self._acumular_insumos(
                componente.elemento_produccion,
                cantidad * componente.cantidad,
                insumos,
                visitados,
            )
        visitados.remove(elemento)

    def _agregar_lineas_bom(
        self,
        elemento,
        cantidad,
        lineas,
        prefijo,
        visitados,
    ):
        if elemento in visitados:
            raise ValueError("La BOM contiene un ciclo")

        visitados.add(elemento)
        componentes = elemento.lista_elementos_bom
        for indice, componente in enumerate(componentes):
            es_ultimo = indice == len(componentes) - 1
            conector = "`-- " if es_ultimo else "+-- "
            cantidad_componente = cantidad * componente.cantidad
            lineas.append(
                f"{prefijo}{conector}"
                f"{componente.elemento_produccion.nombre} x {cantidad_componente}"
            )
            nuevo_prefijo = prefijo + ("    " if es_ultimo else "|   ")
            self._agregar_lineas_bom(
                componente.elemento_produccion,
                cantidad_componente,
                lineas,
                nuevo_prefijo,
                visitados,
            )
        visitados.remove(elemento)

    def explotar(self, elemento, cantidad, inventario=None, consumos_stock=None):
        """Calcula los requerimientos planos de una cantidad del elemento.

        La BOM original se conserva en los productos. Cuando se recibe un
        inventario, el resultado es neto: se descuenta el stock disponible de
        cada subproducto y solo se recorren sus componentes para cubrir el
        faltante.
        """
        requerimientos = {}
        stock_disponible = {}
        self._agregar_requerimientos(
            elemento,
            cantidad,
            requerimientos,
            set(),
            inventario,
            stock_disponible,
            consumos_stock,
        )
        return requerimientos

    def _agregar_requerimientos(
        self,
        elemento,
        cantidad,
        requerimientos,
        visitados,
        inventario=None,
        stock_disponible=None,
        consumos_stock=None,
    ):
        # Un subproducto disponible evita fabricar esa cantidad y, por lo
        # tanto, también evita solicitar sus componentes en la BOM.
        if inventario is not None and elemento.lista_elementos_bom:
            disponible = stock_disponible.get(elemento)
            if disponible is None:
                disponible = max(
                    elemento.stock_total - elemento.stock_reservado,
                    0,
                )
            cantidad_usada = min(cantidad, disponible)
            stock_disponible[elemento] = disponible - cantidad_usada
            if consumos_stock is not None and cantidad_usada:
                consumos_stock[elemento] = (
                    consumos_stock.get(elemento, 0) + cantidad_usada
                )
            cantidad -= cantidad_usada

        if cantidad == 0:
            return

        if not elemento.lista_elementos_bom:
            # Los elementos sin BOM son los insumos que Inventario debe
            # verificar, reservar y consumir.
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
                inventario,
                stock_disponible,
                consumos_stock,
            )
        visitados.remove(elemento)
