class Inventario:
    def hay_stock(self, requerimientos):
        """Indica si hay stock libre para todos los requerimientos planos."""
        for elemento, cantidad in requerimientos.items():
            if not elemento.hay_stock_suficiente(cantidad):
                return False
        return True

    def reservar(self, requerimientos):
        """Reserva las cantidades calculadas por la explosión de la BOM."""
        for elemento, cantidad in requerimientos.items():
            elemento.stock_reservado += cantidad

    def consumir(self, requerimientos):
        """Consume las cantidades previamente reservadas."""
        for elemento, cantidad in requerimientos.items():
            elemento.stock_total -= cantidad
            elemento.stock_reservado -= cantidad