from datetime import datetime

from src.excepciones import (
    CantidadInvalidaError,
    EstadoSolicitudError,
    PeriodoOcupadoError,
    TipoInvalidoError,
)


class ProcesoManufactura:
    def __init__(self, producto):
        self.producto = producto
        self.tareas = []

    def agregar_tarea(self, tarea):
        if tarea is None:
            raise TipoInvalidoError("La tarea no puede ser nula")
        self.tareas.append(tarea)
        return tarea

    def agregar_proceso(self, tarea):
        return self.agregar_tarea(tarea)

    def modificar_proceso(self, tareas):
        if not isinstance(tareas, list):
            raise TipoInvalidoError("Debe recibir una lista de tareas")
        self.tareas = tareas
        return self.tareas

    def calcular_costo_operativo(self):
        costo_total = 0
        for tarea in self.tareas:
            costo_total += tarea.costo_operativo()
        return costo_total


class TareaDefinida:
    def __init__(self, nombre, tiempo, unidad_trabajo, colaboradores_requeridos, habilidades_requeridas):
        self.nombre = nombre
        self.tiempo = tiempo
        self.unidad_trabajo = unidad_trabajo
        self.colaboradores_requeridos = colaboradores_requeridos or []
        self.habilidades_requeridas = habilidades_requeridas or []
        self.subtareas = []

    def agregar_subtarea(self, subtarea):
        if subtarea is None:
            raise TipoInvalidoError("La subtarea no puede ser nula")
        self.subtareas.append(subtarea)
        return subtarea

    def validar_habilidades(self, colaboradores):
        if not isinstance(colaboradores, list):
            raise TipoInvalidoError("Los colaboradores deben enviarse en una lista")

        for habilidad in self.habilidades_requeridas:
            if not any(colaborador.tiene_habilidad(habilidad) for colaborador in colaboradores):
                return False
        return True

    def cantidad_colaboradores_suficiente(self, colaboradores):
        if not isinstance(colaboradores, list):
            raise TipoInvalidoError("Los colaboradores deben enviarse en una lista")
        return len(colaboradores) >= len(self.colaboradores_requeridos)

    def costo_operativo(self):
        if self.unidad_trabajo is None:
            return 0

        costo_ut = self.unidad_trabajo.costo_fijo
        costo_colaboradores = 0

        for colaborador in self.colaboradores_requeridos:
            costo_colaboradores += colaborador.costo_por_hora * self.tiempo

        return costo_ut + costo_colaboradores


class TareaEnCurso:
    ESTADOS_VALIDOS = {"pendiente", "en_curso", "pausada", "finalizada", "cancelada"}

    def __init__(self, nombre, tarea_base, estado):
        self.nombre = nombre
        self.tarea_base = tarea_base
        self.estado = estado
        self.colaboradores = []
        self.unidades_trabajo = []
        self.historial_estados = [estado]

    def actualizar_estado(self, estado):
        if estado not in self.ESTADOS_VALIDOS:
            raise EstadoSolicitudError("Estado no válido")
        self.estado = estado
        self.historial_estados.append(estado)

    def asignar_colaboradores(self, colaboradores):
        if not isinstance(colaboradores, list):
            raise TipoInvalidoError("Los colaboradores deben enviarse en una lista")
        self.colaboradores = colaboradores

    def asignar_UTs(self, unidades_trabajo):
        if not isinstance(unidades_trabajo, list):
            raise TipoInvalidoError("Las unidades de trabajo deben enviarse en una lista")
        self.unidades_trabajo = unidades_trabajo


class UnidadTrabajo:
    def __init__(self, nombre, capacidad_max_produccion, costo_fijo, capacidad_colaboradores):
        self.nombre = nombre
        self.capacidad_max_produccion = capacidad_max_produccion
        self.costo_fijo = costo_fijo
        self.capacidad_colaboradores = capacidad_colaboradores
        self.periodos_ocupados = []

    def asignar_periodo(self, periodo):
        if not isinstance(periodo, PeriodoOperacion):
            raise TipoInvalidoError("Debe asignarse un PeriodoOperacion")
        self.periodos_ocupados.append(periodo)

    def verificar_capacidad(self, cantidad, periodo=None, colaboradores=None):
        if cantidad <= 0:
            raise CantidadInvalidaError("La cantidad debe ser mayor que cero")

        if cantidad > self.capacidad_max_produccion:
            return False

        if colaboradores is not None:
            if not isinstance(colaboradores, list):
                raise TipoInvalidoError("Los colaboradores deben enviarse en una lista")
            if len(colaboradores) > self.capacidad_colaboradores:
                return False

        if periodo is not None:
            for periodo_ocupado in self.periodos_ocupados:
                if periodo.se_solapa_con(periodo_ocupado):
                    return False

        return True


class Colaborador:
    def __init__(self, nombre, costo_por_hora, habilidades):
        self.nombre = nombre
        self.costo_por_hora = costo_por_hora
        self.habilidades = habilidades or []
        self.periodos_ocupados = []

    def tiene_habilidad(self, habilidad):
        return habilidad in self.habilidades

    def asignar_periodo(self, periodo):
        if not isinstance(periodo, PeriodoOperacion):
            raise TipoInvalidoError("Debe asignarse un PeriodoOperacion")
        self.periodos_ocupados.append(periodo)

    def verificar_disponibilidad(self, periodo):
        if not isinstance(periodo, PeriodoOperacion):
            raise TipoInvalidoError("Debe verificarse con un PeriodoOperacion")

        for periodo_ocupado in self.periodos_ocupados:
            if periodo.se_solapa_con(periodo_ocupado):
                return False
        return True


class PeriodoOperacion:
    def __init__(self, inicio, fin):
        if not isinstance(inicio, datetime) or not isinstance(fin, datetime):
            raise TipoInvalidoError("Inicio y fin deben ser datetime")
        if fin <= inicio:
            raise PeriodoOcupadoError("La fecha fin debe ser posterior a la fecha inicio")
        self.inicio = inicio
        self.fin = fin

    def duracion_horas(self):
        diferencia = self.fin - self.inicio
        return diferencia.total_seconds() / 3600

    def se_solapa_con(self, otro):
        if not isinstance(otro, PeriodoOperacion):
            raise TipoInvalidoError("Debe compararse con otro PeriodoOperacion")
        return not (self.fin <= otro.inicio or otro.fin <= self.inicio)