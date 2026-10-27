class NodoCola:
    def __init__(self, dato):
        self.dato = dato
        self.siguiente = None


class ColaFIFO:
    def __init__(self):
        self.primero = None
        self.ultimo = None
        self.cantidad = 0

    def encolar(self, dato):
        nodo = NodoCola(dato)
        if self.ultimo is None:
            self.primero = nodo
        else:
            self.ultimo.siguiente = nodo
        self.ultimo = nodo
        self.cantidad += 1

    def desencolar(self):
        if self.primero is None:
            raise IndexError("No se puede desencolar una cola vacía")

        dato = self.primero.dato
        self.primero = self.primero.siguiente
        if self.primero is None:
            self.ultimo = None
        self.cantidad -= 1
        return dato

    def ver_primero(self):
        if self.primero is None:
            raise IndexError("No se puede consultar una cola vacía")
        return self.primero.dato

    def __bool__(self):
        return self.primero is not None

    def __len__(self):
        return self.cantidad