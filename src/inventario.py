class Inventario:
    def __init__(self):
        self.stock = {}

    def registrar(self, elemento, stock_actual=0, stock_reservado=0):
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
        for elemento, cantidad in requerimientos.items():
            if self.stock_libre(elemento) < cantidad:
                return False
        return True

    def reservar(self, requerimientos):
        """Reserva las cantidades calculadas por la explosión de la BOM."""
        for elemento, cantidad in requerimientos.items():
            self.obtener_stock(elemento)["reservado"] += cantidad

    def consumir(self, requerimientos):
        """Consume las cantidades previamente reservadas."""
        for elemento, cantidad in requerimientos.items():
            datos = self.obtener_stock(elemento)
            datos["actual"] -= cantidad
            datos["reservado"] -= cantidad

    def agregar_stock(self, elemento, cantidad):
        self.obtener_stock(elemento)["actual"] += cantidad