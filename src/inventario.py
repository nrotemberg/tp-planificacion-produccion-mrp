from src.excepciones import CantidadInvalidaError, StockInsuficienteError, TipoInvalidoError


class Inventario:
    def __init__(self):
        self.stock = {}

    def registrar(self, elemento, stock_actual=0, stock_reservado=0):
        self._validar_cantidad(stock_actual, "El stock actual", permitir_cero=True)
        self._validar_cantidad(
            stock_reservado,
            "El stock reservado",
            permitir_cero=True,
        )
        if stock_reservado > stock_actual:
            raise CantidadInvalidaError(
                "El stock reservado no puede superar el stock actual"
            )
        if elemento in self.stock:
            return False
        self.stock[elemento] = {
            "actual": stock_actual,
            "reservado": stock_reservado,
        }
        return True

    def obtener_stock(self, elemento):
        return self.stock[elemento]

    def stock_libre(self, elemento):
        datos = self.obtener_stock(elemento)
        return datos["actual"] - datos["reservado"]

    def hay_stock(self, requerimientos):
        """Indica si hay stock libre para todos los requerimientos planos."""
        items = self._validar_requerimientos(requerimientos)
        return all(
            self.stock_libre(elemento) >= cantidad
            for elemento, cantidad in items
        )

    def reservar(self, requerimientos):
        """Reserva las cantidades calculadas por la explosión de la BOM."""
        items = self._validar_requerimientos(requerimientos)
        for elemento, cantidad in items:
            if self.stock_libre(elemento) < cantidad:
                raise StockInsuficienteError(
                    f"No hay stock libre suficiente de '{elemento.nombre}'"
                )
        for elemento, cantidad in items:
            self.obtener_stock(elemento)["reservado"] += cantidad

    def consumir(self, requerimientos):
        """Consume las cantidades previamente reservadas."""
        items = self._validar_requerimientos(requerimientos)
        for elemento, cantidad in items:
            datos = self.obtener_stock(elemento)
            if datos["actual"] < cantidad or datos["reservado"] < cantidad:
                raise StockInsuficienteError(
                    f"No hay stock reservado suficiente de '{elemento.nombre}'"
                )
        for elemento, cantidad in items:
            datos = self.obtener_stock(elemento)
            datos["actual"] -= cantidad
            datos["reservado"] -= cantidad

    def liberar_reserva(self, requerimientos):
        """Libera reservas sin retirar las unidades del inventario."""
        items = self._validar_requerimientos(requerimientos)
        for elemento, cantidad in items:
            if self.obtener_stock(elemento)["reservado"] < cantidad:
                raise StockInsuficienteError(
                    f"No hay stock reservado suficiente de '{elemento.nombre}'"
                )
        for elemento, cantidad in items:
            self.obtener_stock(elemento)["reservado"] -= cantidad

    def agregar_stock(self, elemento, cantidad):
        self._validar_cantidad(cantidad, "La cantidad a agregar")
        self.obtener_stock(elemento)["actual"] += cantidad

    @staticmethod
    def _validar_cantidad(cantidad, campo, permitir_cero=False):
        if not isinstance(cantidad, int) or isinstance(cantidad, bool):
            raise CantidadInvalidaError(f"{campo} debe ser un entero")
        if cantidad < 0 or (cantidad == 0 and not permitir_cero):
            calificador = "no puede ser negativa" if permitir_cero else "debe ser positiva"
            raise CantidadInvalidaError(f"{campo} {calificador}")

    def _validar_requerimientos(self, requerimientos):
        if not isinstance(requerimientos, dict):
            raise TipoInvalidoError("Los requerimientos deben ser un diccionario")

        items = list(requerimientos.items())
        for elemento, cantidad in items:
            self.obtener_stock(elemento)
            self._validar_cantidad(cantidad, "La cantidad requerida")
        return items