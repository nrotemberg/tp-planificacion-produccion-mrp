class Inventario:
    def hay_stock(self, requerimientos):
        for elemento, cantidad in requerimientos.items():
            if not elemento.hay_stock_suficiente(cantidad):
                return False
        return True

    def reservar(self, requerimientos):
        for elemento, cantidad in requerimientos.items():
            elemento.stock_reservado += cantidad

    def consumir(self, requerimientos):
        for elemento, cantidad in requerimientos.items():
            elemento.stock_total -= cantidad
            elemento.stock_reservado -= cantidad
