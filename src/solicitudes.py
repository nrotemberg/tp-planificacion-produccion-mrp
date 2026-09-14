class Solicitud:
    def __init__(self, id, solicitante, estado, producto, cantidad):
        self.id = id
        self.solicitante = solicitante
        self.estado = estado
        self.producto = producto
        self.cantidad = cantidad

        if not isinstance(cantidad, int) or cantidad <= 0:
            raise ValueError("La cantidad debe ser un entero positivo")

    def cambiar_estado(self, nuevo_estado):
        self.estado = nuevo_estado
