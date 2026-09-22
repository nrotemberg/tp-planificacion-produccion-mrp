class Solicitud:
    def __init__(self, id, solicitante, producto, cantidad, **parametros):
        if not isinstance(cantidad, int) or cantidad <= 0:
            raise ValueError("La cantidad debe ser un entero positivo")
        self.id = id
        self.solicitante = solicitante
        self.estado = "creada"
        self.producto = producto
        self.cantidad = cantidad
        self.parametros = parametros


    def cambiar_estado(self):
        transiciones = {"creada": "planificada", "planificada": "en curso", "en curso": "finalizada"}

        siguiente_estado = transiciones.get(self.estado)

        if siguiente_estado is None:
            return False

        self.estado = siguiente_estado
        return True