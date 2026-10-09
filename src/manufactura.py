from datetime import datetime

from src.elementos import Producto
from src.excepciones import (
    CantidadInvalidaError,
    ColaboradorNoDisponibleError,
    CostoInvalidoError,
    ElementoDuplicadoError,
    EstadoSolicitudError,
    HabilidadRequeridaError,
    PeriodoOcupadoError,
    RecursosInsuficientesError,
    TipoInvalidoError,
)


class ProcesoManufactura:
    def __init__(self, producto):
        if not isinstance(producto, Producto):
            raise TipoInvalidoError("El producto debe ser una instancia de Producto")
        self.producto = producto
        self.tareas = []

    def agregar_tarea(self, tarea):
        if not isinstance(tarea, TareaDefinida):
            raise TipoInvalidoError("Debe recibir una instancia de TareaDefinida")
        if tarea in self.tareas:
            raise ElementoDuplicadoError("La tarea ya está agregada al proceso")
        self.tareas.append(tarea)
        return tarea

    def modificar_proceso(self, tareas):
        if not isinstance(tareas, list) or any(not isinstance(tarea, TareaDefinida) for tarea in tareas):
            raise TipoInvalidoError("Debe recibir una lista de instancias de TareaDefinida")
        if len(set(map(id, tareas))) != len(tareas):
            raise ElementoDuplicadoError("La lista no puede contener tareas repetidas")
        self.tareas = list(tareas)
        return list(self.tareas)

    def iniciar_proceso(self, cantidad, periodos):
        if cantidad <= 0:
            raise CantidadInvalidaError("La cantidad debe ser mayor que cero")
        if not isinstance(periodos, list):
            raise TipoInvalidoError("Los períodos deben enviarse en una lista")
        if len(periodos) != len(self.tareas):
            raise TipoInvalidoError("Debe existir un período por cada tarea")
        if any(not isinstance(periodo, PeriodoOperacion) for periodo in periodos):
            raise TipoInvalidoError("Todos los períodos deben ser PeriodoOperacion")

        posiciones = {id(tarea): posicion for posicion, tarea in enumerate(self.tareas)}
        self._validar_dependencias(posiciones)

        asignaciones = []
        reservas_pendientes = []
        for tarea, periodo in zip(self.tareas, periodos):
            colaboradores = list(tarea.colaboradores_requeridos)
            if not tarea.validar_habilidades(colaboradores):
                raise HabilidadRequeridaError(
                    f"La tarea '{tarea.nombre}' no tiene las habilidades requeridas"
                )
            if not tarea.cantidad_colaboradores_suficiente(colaboradores):
                raise RecursosInsuficientesError(
                    f"La tarea '{tarea.nombre}' no tiene suficientes colaboradores"
                )
            if any(not colaborador.verificar_disponibilidad(periodo) for colaborador in colaboradores):
                raise ColaboradorNoDisponibleError(
                    f"No hay colaboradores disponibles para la tarea '{tarea.nombre}'"
                )
            if tarea.unidad_trabajo is not None and not tarea.unidad_trabajo.verificar_capacidad(
                cantidad,
                periodo=periodo,
                colaboradores=colaboradores,
            ):
                raise RecursosInsuficientesError(
                    f"La unidad de trabajo no tiene capacidad para la tarea '{tarea.nombre}'"
                )
            for colaborador in colaboradores:
                self._validar_conflicto_reserva(
                    colaborador,
                    periodo,
                    reservas_pendientes,
                    ColaboradorNoDisponibleError(
                        f"El colaborador '{colaborador.nombre}' tiene una reserva superpuesta"
                    ),
                )
            if tarea.unidad_trabajo is not None:
                self._validar_conflicto_reserva(
                    tarea.unidad_trabajo,
                    periodo,
                    reservas_pendientes,
                    PeriodoOcupadoError(
                        f"La unidad de trabajo '{tarea.unidad_trabajo.nombre}' tiene una reserva superpuesta"
                    ),
                )
            asignaciones.append((tarea, periodo, colaboradores))
            reservas_pendientes.extend((colaborador, periodo) for colaborador in colaboradores)
            if tarea.unidad_trabajo is not None:
                reservas_pendientes.append((tarea.unidad_trabajo, periodo))

        tareas_en_curso = []
        for tarea, periodo, colaboradores in asignaciones:
            if tarea.unidad_trabajo is not None:
                tarea.unidad_trabajo.asignar_periodo(periodo)
            for colaborador in colaboradores:
                colaborador.asignar_periodo(periodo)

            tarea_en_curso = TareaEnCurso(tarea.nombre, tarea, "pendiente")
            tarea_en_curso.asignar_colaboradores(colaboradores)
            if tarea.unidad_trabajo is not None:
                tarea_en_curso.asignar_UTs([tarea.unidad_trabajo])
            tareas_en_curso.append(tarea_en_curso)

        return tareas_en_curso

    def _validar_dependencias(self, posiciones):
        estados = {}

        def visitar(tarea):
            tarea_id = id(tarea)
            if estados.get(tarea_id) == "visitando":
                raise TipoInvalidoError("Las subtareas no pueden formar ciclos")
            if estados.get(tarea_id) == "validada":
                return

            estados[tarea_id] = "visitando"
            for subtarea in tarea.subtareas:
                if not isinstance(subtarea, TareaDefinida):
                    raise TipoInvalidoError("Todas las subtareas deben ser TareaDefinida")
                if id(subtarea) not in posiciones:
                    raise TipoInvalidoError("Todas las subtareas deben pertenecer al proceso")
                visitar(subtarea)
                if posiciones[id(subtarea)] >= posiciones[id(tarea)]:
                    raise TipoInvalidoError("Las subtareas deben preceder a su tarea padre")
            estados[tarea_id] = "validada"

        for tarea in self.tareas:
            visitar(tarea)

    @staticmethod
    def _validar_conflicto_reserva(recurso, periodo, reservas_pendientes, error):
        for recurso_reservado, periodo_reservado in reservas_pendientes:
            if recurso is recurso_reservado and periodo.se_solapa_con(periodo_reservado):
                raise error

    def calcular_costo_operativo(self):
        costo_total = 0
        for tarea in self.tareas:
            costo_total += tarea.costo_operativo()
        return costo_total


class TareaDefinida:
    def __init__(self, nombre, tiempo, unidad_trabajo, colaboradores_requeridos, habilidades_requeridas):
        if not isinstance(nombre, str) or not nombre.strip():
            raise TipoInvalidoError("El nombre de la tarea debe ser un texto no vacío")
        if isinstance(tiempo, bool) or not isinstance(tiempo, (int, float)):
            raise TipoInvalidoError("El tiempo de la tarea debe ser numérico")
        if tiempo <= 0:
            raise CantidadInvalidaError("El tiempo de la tarea debe ser mayor que cero")
        if unidad_trabajo is not None and not isinstance(unidad_trabajo, UnidadTrabajo):
            raise TipoInvalidoError("La unidad de trabajo debe ser una UnidadTrabajo")
        if colaboradores_requeridos is not None:
            self._validar_colaboradores(colaboradores_requeridos)
        if habilidades_requeridas is not None and not isinstance(habilidades_requeridas, list):
            raise TipoInvalidoError("Las habilidades requeridas deben enviarse en una lista")
        if habilidades_requeridas is not None and any(
            not isinstance(habilidad, str) or not habilidad.strip()
            for habilidad in habilidades_requeridas
        ):
            raise TipoInvalidoError("Todas las habilidades requeridas deben ser textos no vacíos")

        self.nombre = nombre
        self.tiempo = tiempo
        self.unidad_trabajo = unidad_trabajo
        self.colaboradores_requeridos = colaboradores_requeridos or []
        self.habilidades_requeridas = habilidades_requeridas or []
        self.subtareas = []

    def agregar_subtarea(self, subtarea):
        if not isinstance(subtarea, TareaDefinida):
            raise TipoInvalidoError("La subtarea debe ser una instancia de TareaDefinida")
        if subtarea in self.subtareas:
            raise ElementoDuplicadoError("La subtarea ya está agregada")
        if subtarea is self or self._contiene_tarea(subtarea, self):
            raise TipoInvalidoError("Las subtareas no pueden formar ciclos")
        self.subtareas.append(subtarea)
        return subtarea

    @staticmethod
    def _contiene_tarea(tarea, objetivo, visitadas=None):
        if tarea is objetivo:
            return True
        if visitadas is None:
            visitadas = set()
        if id(tarea) in visitadas:
            return False

        visitadas.add(id(tarea))
        return any(
            isinstance(subtarea, TareaDefinida)
            and TareaDefinida._contiene_tarea(subtarea, objetivo, visitadas)
            for subtarea in tarea.subtareas
        )

    def validar_habilidades(self, colaboradores):
        self._validar_colaboradores(colaboradores)

        for habilidad in self.habilidades_requeridas:
            if not any(colaborador.tiene_habilidad(habilidad) for colaborador in colaboradores):
                return False
        return True

    def cantidad_colaboradores_suficiente(self, colaboradores):
        self._validar_colaboradores(colaboradores)
        return len(colaboradores) >= len(self.colaboradores_requeridos)

    @staticmethod
    def _validar_colaboradores(colaboradores):
        if not isinstance(colaboradores, list):
            raise TipoInvalidoError("Los colaboradores deben enviarse en una lista")
        if any(not isinstance(colaborador, Colaborador) for colaborador in colaboradores):
            raise TipoInvalidoError("Todos los colaboradores deben ser Colaborador")
        if len(set(map(id, colaboradores))) != len(colaboradores):
            raise ElementoDuplicadoError("La lista no puede contener colaboradores repetidos")

    def costo_operativo(self):
        costo_ut = 0
        if self.unidad_trabajo is not None:
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
        if (
            isinstance(costo_fijo, bool)
            or not isinstance(costo_fijo, (int, float))
            or costo_fijo < 0
        ):
            raise CostoInvalidoError("El costo fijo debe ser numérico y no negativo")
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
        if (
            isinstance(costo_por_hora, bool)
            or not isinstance(costo_por_hora, (int, float))
            or costo_por_hora < 0
        ):
            raise CostoInvalidoError("El costo por hora debe ser numérico y no negativo")
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