class ProcesoManufactura:
    def __init__(self, producto):
        pass

    def agregar_tarea(self, tarea):
        pass

    def agregar_proceso(self, tarea):
        pass

    def modificar_proceso(self, tareas):
        pass

    def calcular_costo_operativo(self):
        pass


class TareaDefinida:
    def __init__(self, nombre, tiempo, unidad_trabajo, colaboradores_requeridos, habilidades_requeridas):
        pass

    def agregar_tarea(self, tarea):
        pass

    def costo_operativo(self):
        pass


class TareaEnCurso:
    def __init__(self, nombre, tarea_base, estado):
        pass

    def actualizar_estado(self, estado):
        pass

    def asignar_colaboradores(self, colaboradores):
        pass

    def asignar_UTs(self, unidades_trabajo):
        pass


class UnidadTrabajo:
    def __init__(self, nombre, capacidad_max_produccion, costo_fijo, capacidad_colaboradores):
        pass

    def verificar_capacidad(self, cantidad):
        pass


class Colaborador:
    def __init__(self, nombre, costo_por_hora, habilidades):
        pass

    def tiene_habilidad(self, habilidad):
        pass

    def verificar_disponibilidad(self, periodo):
        pass


class PeriodoOperacion:
    def __init__(self, inicio, fin):
        pass

    def duracion_horas(self):
        pass

    def se_solapa_con(self, otro):
        pass