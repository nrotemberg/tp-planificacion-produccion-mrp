from datetime import datetime

import pytest

from src.excepciones import (
    ColaboradorNoDisponibleError,
    ElementoDuplicadoError,
    EstadoSolicitudError,
    HabilidadRequeridaError,
    PeriodoOcupadoError,
    RecursosInsuficientesError,
    TipoInvalidoError,
)
from src.manufactura import Colaborador, PeriodoOperacion, TareaDefinida, TareaEnCurso, UnidadTrabajo


def crear_tarea_base():
    ut = UnidadTrabajo("Molino", 100, 50, 3)
    colaborador_1 = Colaborador("Ana", 30, ["corte", "soldadura"])
    colaborador_2 = Colaborador("Luis", 25, ["corte"])
    return TareaDefinida("Corte", 4, ut, [colaborador_1, colaborador_2], ["corte"])


def crear_tarea_en_curso(nombre="Corte", tarea_base=None, estado="pendiente"):
    if tarea_base is None:
        tarea_base = crear_tarea_base()
    return TareaEnCurso(nombre, tarea_base, estado)


def test_crear_tarea_en_curso_validacion_de_tarea_base_y_estado():
    tarea_base = crear_tarea_base()

    tarea = crear_tarea_en_curso(tarea_base=tarea_base)

    assert tarea.nombre == "Corte"
    assert tarea.tarea_base is tarea_base
    assert tarea.estado == "pendiente"
    assert tarea.colaboradores == []
    assert tarea.unidades_trabajo == []
    assert tarea.historial_estados == ["pendiente"]

    with pytest.raises(TipoInvalidoError, match="TareaDefinida"):
        TareaEnCurso("Corte", object(), "pendiente")

    with pytest.raises(EstadoSolicitudError, match="Estado no válido"):
        TareaEnCurso("Corte", tarea_base, "estado_invalido")


@pytest.mark.parametrize(
    ("estado_inicial", "nuevo_estado"),
    [("pendiente", "en_curso"), ("en_curso", "pausada"), ("pausada", "en_curso"), ("en_curso", "finalizada"), ("en_curso", "cancelada")],
)
def test_actualizar_estado_acepta_transiciones_validas(estado_inicial, nuevo_estado):
    tarea = crear_tarea_en_curso(estado=estado_inicial)

    tarea.actualizar_estado(nuevo_estado)

    assert tarea.estado == nuevo_estado
    assert tarea.historial_estados == [estado_inicial, nuevo_estado]


def test_actualizar_estado_rechaza_transiciones_invalidas_y_conserva_historial():
    tarea = crear_tarea_en_curso(estado="en_curso")
    historial_esperado = ["en_curso"]

    with pytest.raises(EstadoSolicitudError, match="Transición de estado no válida"):
        tarea.actualizar_estado("pendiente")

    assert tarea.estado == "en_curso"
    assert tarea.historial_estados == historial_esperado


def test_asignar_colaboradores_y_UTs_con_validacion_de_recursos():
    tarea_base = crear_tarea_base()
    tarea = TareaEnCurso("Corte", tarea_base, "pendiente")
    periodo = PeriodoOperacion(datetime(2024, 1, 1, 9), datetime(2024, 1, 1, 11))
    colaboradores = list(tarea_base.colaboradores_requeridos)
    ut = tarea_base.unidad_trabajo

    tarea.actualizar_estado("en_curso")
    tarea.asignar_colaboradores(colaboradores, periodo)
    tarea.asignar_UTs([ut], periodo)

    assert tarea.colaboradores == colaboradores
    assert tarea.unidades_trabajo == [ut]
    assert all(periodo in colaborador.periodos_ocupados for colaborador in colaboradores)
    assert periodo in ut.periodos_ocupados

    with pytest.raises(TipoInvalidoError, match="lista"):
        tarea.asignar_colaboradores(None)

    with pytest.raises(ElementoDuplicadoError, match="repetidos"):
        tarea.asignar_colaboradores([colaboradores[0], colaboradores[0]], periodo)

    tarea_sin_recursos = TareaEnCurso("Corte", tarea_base, "en_curso")
    with pytest.raises(RecursosInsuficientesError):
        tarea_sin_recursos.asignar_colaboradores([colaboradores[0]], periodo)

    tarea_con_colaboradores_duplicados = TareaEnCurso("Corte", tarea_base, "en_curso")
    with pytest.raises(ElementoDuplicadoError):
        tarea_con_colaboradores_duplicados.asignar_colaboradores([colaboradores[0], colaboradores[0]], periodo)


def test_asignar_recursos_falla_por_disponibilidad_y_capacidad():
    tarea_base = crear_tarea_base()
    tarea = TareaEnCurso("Corte", tarea_base, "pendiente")
    periodo = PeriodoOperacion(datetime(2024, 1, 1, 9), datetime(2024, 1, 1, 11))
    periodo_superpuesto = PeriodoOperacion(datetime(2024, 1, 1, 10), datetime(2024, 1, 1, 12))
    colaborador_1 = tarea_base.colaboradores_requeridos[0]
    colaborador_2 = tarea_base.colaboradores_requeridos[1]

    tarea.actualizar_estado("en_curso")
    colaborador_1.asignar_periodo(periodo_superpuesto)

    with pytest.raises(ColaboradorNoDisponibleError):
        tarea.asignar_colaboradores([colaborador_1, colaborador_2], periodo)

    ut = tarea_base.unidad_trabajo
    ut.asignar_periodo(periodo_superpuesto)
    with pytest.raises(PeriodoOcupadoError):
        tarea.asignar_UTs([ut], periodo)


def test_finalizar_y_cancelar_liberan_recursos_asignados():
    tarea_base = crear_tarea_base()
    tarea = TareaEnCurso("Corte", tarea_base, "pendiente")
    periodo = PeriodoOperacion(datetime(2024, 1, 1, 9), datetime(2024, 1, 1, 11))
    colaboradores = list(tarea_base.colaboradores_requeridos)
    ut = tarea_base.unidad_trabajo

    tarea.actualizar_estado("en_curso")
    tarea.asignar_colaboradores(colaboradores, periodo)
    tarea.asignar_UTs([ut], periodo)

    tarea.finalizar()
    assert tarea.estado == "finalizada"
    assert tarea.colaboradores == []
    assert tarea.unidades_trabajo == []
    for colaborador in colaboradores:
        assert colaborador.periodos_ocupados == []
    assert ut.periodos_ocupados == []

    otra_tarea = TareaEnCurso("Corte", tarea_base, "pendiente")
    otra_tarea.actualizar_estado("en_curso")
    otra_tarea.asignar_colaboradores(colaboradores, periodo)
    otra_tarea.asignar_UTs([ut], periodo)
    otra_tarea.cancelar()

    assert otra_tarea.estado == "cancelada"
    assert otra_tarea.colaboradores == []
    assert otra_tarea.unidades_trabajo == []


def test_liberar_periodo_inexistente_rechaza_la_operacion():
    tarea_base = crear_tarea_base()
    tarea = TareaEnCurso("Corte", tarea_base, "pendiente")
    periodo = PeriodoOperacion(datetime(2024, 1, 1, 9), datetime(2024, 1, 1, 11))

    with pytest.raises(PeriodoOcupadoError, match="no pertenece"):
        tarea.liberar_recursos(colaboradores=[], unidades_trabajo=[], periodo=periodo)
