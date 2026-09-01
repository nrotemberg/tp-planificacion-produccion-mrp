# Tu implementacion va aqui
class ElementoProduccion: #Clase base para Insumo y Producto
    def __init__(self, nombre, unidad_medida, stock_total, stock_reservado, costo):
        self.nombre = nombre
        self.unidad_medida = unidad_medida
        self.stock_total = stock_total
        self.stock_reservado = stock_reservado
        self.set_costo(costo)

    def set_costo(self, nuevo_costo):
        if not isinstance(nuevo_costo, (int, float)) or nuevo_costo <= 0:
            raise ValueError("El costo debe ser mayor a 0")
        self.costo = nuevo_costo

    def hay_stock_suficiente(self, cantidad_requerida): #Metodo para verificar si hay stock suficiente
        pass

    def costo_unitario(self): #Metodo para obtener el costo unitario del elemento de producción
        pass


class Insumo(ElementoProduccion): #Subclase de ElementoProduccion, representa un insumo que se utiliza en la producción de un producto
    def __init__(self, nombre, unidad_medida, stock_total, stock_reservado, costo):
        super().__init__(nombre, unidad_medida, stock_total, stock_reservado, costo)

    def get_costo(self): #Metodo para obtener el costo del insumo
        return self.costo

    def set_costo(self, nuevo_costo): #Metodo para actualizar el costo del insumo
        if not isinstance(nuevo_costo, (int, float)) or nuevo_costo <= 0:
            raise ValueError("El costo debe ser mayor a 0")
        self.costo = nuevo_costo

    def actualizar_costo(self, nuevo_costo):
        self.set_costo(nuevo_costo)


class ComponenteBOM: #Clase que representa un componente de la lista de materiales (BOM) de un producto
    def __init__(self, elemento_produccion, cantidad):
        self.elemento_produccion = elemento_produccion
        self.set_cantidad(cantidad) #Se utiliza el metodo set_cantidad para validar la cantidad del componente

    def set_cantidad(self, nueva_cantidad): #Metodo para validar que la cantidad del componente sea entera y positiva
        if isinstance(nueva_cantidad, int) and nueva_cantidad > 0:
            self.cantidad = nueva_cantidad
        else:
            raise ValueError("La cantidad debe ser un número entero positivo")
        pass


class Producto(ElementoProduccion): #Subclase de ElementoProduccion, representa un producto que se produce a partir de insumos y componentes
    def __init__(self, nombre, unidad_medida, stock_total, stock_reservado, costo):
            super().__init__(nombre, unidad_medida, stock_total, stock_reservado, costo)
            self.lista_elementos_bom = [] 

    def agregar_a_bom(self, componente): #Metodo para agregar un componente a la lista de elementos BOM del producto
        self.lista_elementos_bom.append(componente)

    def costo_unitario(self): #Metodo para obtener el costo del producto
        costo_total = 0

        for componente in self.lista_elementos_bom:
            elemento = componente.elemento_produccion
            cantidad = componente.cantidad

            if isinstance(elemento, Insumo):
                costo_total += elemento.get_costo() * cantidad
            elif isinstance(elemento, Producto):
                costo_total += elemento.costo_unitario() * cantidad
        self.costo = costo_total

        return costo_total


class ProcesoManufactura: #Clase que representa un proceso de manufactura para un producto
    def __init__(self, producto):
        self.tareas_requeridas = []
        self.producto = producto

    def agregar_proceso(self):
        pass

    def modificar_proceso(self): 
        pass

    def calcular_costo_operativo(self): #Metodo para calcular el costo operativo del proceso de manufactura
        pass


class TareaDefinida: #Clase que representa una tarea especifica dentro de un proceso de manufactura
    def __init__(self, nombre, tiempo, unidad_trabajo, colaboradores_requeridos):
        self.nombre = nombre
        self.tiempo = tiempo
        self.unidad_trabajo = unidad_trabajo
        self.colaboradores_requeridos = colaboradores_requeridos

    def agregar_tarea(self, proceso): #Metodo para agregar una tarea definida a un proceso de manufactura
        pass


class TareaEnCurso: #Clase que representa una tarea en curso dentro de un proceso de manufactura
    def __init__(self, nombre, tarea_base, estado):
        self.nombre = nombre
        self.colaboradores_asignados = []
        self.unidades_trabajo_asignadas = []
        self.tarea_base = tarea_base
        self.estado = estado

    def actualizar_estado(self): #Metodo para actualizar el estado de la solicitud
        pass

    def asignar_colaboradores(self): #Metodo para asignar colaboradores a la tarea
        pass

    def asignar_UTs(self): #Metodo para asignar unidades de trabajo a la tarea
        pass


class UnidadTrabajo: #Clase que representa una unidad de trabajo que puede ser asignada a una tarea
    def __init__(self, nombre, capacidad_max_produccion, costo_fijo, capacidad_colaboradores):
        self.nombre = nombre
        self.capacidad_max_produccion = capacidad_max_produccion
        self.costo_fijo = costo_fijo
        self.capacidad_colaboradores = capacidad_colaboradores
        self.periodos_operacion = []
        self.colaboradores_activos = []
        self.maquinas_disponibles = []

    def verificar_capacidad(self): #Metodo para verificar si la unidad de trabajo tiene capacidad para ser asignada a una tarea
        pass


class Colaborador: #Clase que representa un colaborador que puede ser asignado a una tarea
    def __init__(self, nombre, costo_por_hora):
        self.nombre = nombre
        self.costo_por_hora = costo_por_hora
        self.periodos_operacion = []

    def verificar_disponibilidad(self): #Metodo para verificar si el colaborador está disponible para ser asignado a una tarea en curso
        pass


class PeriodoOperacion: #Clase que representa un periodo de tiempo en el que se realiza una operación, ya sea un trabajador o una maquinaria
    def __init__(self, inicio, fin):
        self.inicio = inicio
        self.fin = fin

    def duracion_horas(self): #Metodo para calcular la duración del periodo de operación en horas
        pass

    def se_solapa_con(self, otro_periodo): # Verifica si dos periodos de operación se superponen (maquinaria <-> trabajador)
        pass


class Solicitud: #Clase que representa una solicitud de producción de un producto
    def __init__(self, id, solicitante, fase, producto, cantidad):
        self.id = id
        self.solicitante = solicitante
        self.fase = fase
        self.producto = producto
        self.cantidad = cantidad

    def verificar_stock(self): #Metodo para verificar si hay stock suficiente de los elementos de producción necesarios para la solicitud
        pass

    def reservar(self): #Metodo para reservar recursos para la solicitud
        pass

    def iniciar_produccion(self): #Metodo para iniciar la producción de la solicitud
        pass

    def consumir_stock(self): #Metodo para consumir el stock del producto solicitado
        pass

    def finalizar_produccion(self): #Metodo para finalizar la producción de la solicitud
        pass

    def detectar_cuello(self): #Metodo para detectar cuellos de botella en la producción
        pass








def hola_mundo():
    return "hola_mundo"


def main():
    # Aqui ejecutas tus soluciones
    print(hola_mundo())


# No cambiar a partir de aqui
if __name__ == "__main__":
    main()
