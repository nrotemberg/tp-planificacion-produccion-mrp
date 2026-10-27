from datetime import datetime

import pytest

from src.manufactura import Colaborador, PeriodoOperacion, UnidadTrabajo
from src.excepciones import (
	CantidadInvalidaError,
	CostoInvalidoError,
	ElementoDuplicadoError,
	PeriodoOcupadoError,
	TipoInvalidoError,
)


def crear_unidad_trabajo(
	nombre="Torno",
	capacidad_max_produccion=10,
	costo_fijo=300,
	capacidad_colaboradores=2,
):
	return UnidadTrabajo(
		nombre,
		capacidad_max_produccion,
		costo_fijo,
		capacidad_colaboradores,
	)


def crear_periodo(hora_inicio, hora_fin):
	return PeriodoOperacion(
		datetime(2026, 9, 22, hora_inicio),
		datetime(2026, 9, 22, hora_fin),
	)


def test_crear_unidad_trabajo_inicializa_sus_atributos():
	unidad = crear_unidad_trabajo()

	assert unidad.nombre == "Torno"
	assert unidad.capacidad_max_produccion == 10
	assert unidad.costo_fijo == 300
	assert unidad.capacidad_colaboradores == 2
	assert unidad.periodos_ocupados == []


def test_crear_unidad_trabajo_rechaza_costo_fijo_negativo():
	with pytest.raises(CostoInvalidoError, match="costo fijo"):
		crear_unidad_trabajo(costo_fijo=-1)


@pytest.mark.parametrize("nombre", ["", "   ", None, 123])
def test_crear_unidad_trabajo_rechaza_nombre_invalido(nombre):
	with pytest.raises(TipoInvalidoError, match="nombre"):
		crear_unidad_trabajo(nombre=nombre)


@pytest.mark.parametrize("capacidad", [0, -1, True, float("nan"), float("inf"), "10"])
def test_crear_unidad_trabajo_rechaza_capacidad_invalida(capacidad):
	with pytest.raises((CantidadInvalidaError, TipoInvalidoError)):
		crear_unidad_trabajo(capacidad_max_produccion=capacidad)


@pytest.mark.parametrize("costo", [0, -1, True, float("nan"), float("inf"), "300"])
def test_crear_unidad_trabajo_rechaza_costo_invalido(costo):
	with pytest.raises(CostoInvalidoError):
		crear_unidad_trabajo(costo_fijo=costo)


@pytest.mark.parametrize("capacidad", [-1, True, 1.5, "2"])
def test_crear_unidad_trabajo_rechaza_capacidad_de_colaboradores_invalida(capacidad):
	with pytest.raises((CantidadInvalidaError, TipoInvalidoError)):
		crear_unidad_trabajo(capacidad_colaboradores=capacidad)


def test_asignar_periodo_agrega_un_periodo_valido():
	unidad = crear_unidad_trabajo()
	periodo = crear_periodo(8, 10)

	unidad.asignar_periodo(periodo)

	assert unidad.periodos_ocupados == [periodo]


def test_asignar_periodo_rechaza_un_valor_invalido():
	unidad = crear_unidad_trabajo()

	with pytest.raises(TipoInvalidoError, match="Debe asignarse un PeriodoOperacion"):
		unidad.asignar_periodo("08:00-10:00")

	assert unidad.periodos_ocupados == []


def test_asignar_periodo_rechaza_solapamiento_sin_modificar_reservas():
	unidad = crear_unidad_trabajo()
	periodo = crear_periodo(8, 10)
	unidad.asignar_periodo(periodo)

	with pytest.raises(PeriodoOcupadoError):
		unidad.asignar_periodo(crear_periodo(9, 11))

	assert unidad.periodos_ocupados == [periodo]


def test_verificar_capacidad_acepta_cantidad_dentro_del_limite():
	unidad = crear_unidad_trabajo()

	assert unidad.verificar_capacidad(10) is True


@pytest.mark.parametrize("cantidad", [0, -1, True, float("nan"), float("inf"), "5"])
def test_verificar_capacidad_rechaza_cantidades_no_positivas(cantidad):
	unidad = crear_unidad_trabajo()

	with pytest.raises(CantidadInvalidaError, match="debe ser mayor que cero"):
		unidad.verificar_capacidad(cantidad)


def test_verificar_capacidad_devuelve_false_si_supera_la_produccion_maxima():
	unidad = crear_unidad_trabajo(capacidad_max_produccion=10)

	assert unidad.verificar_capacidad(11) is False


def test_verificar_capacidad_acepta_colaboradores_dentro_del_limite():
	unidad = crear_unidad_trabajo(capacidad_colaboradores=2)

	colaboradores = [Colaborador("Ana", 1, []), Colaborador("Luis", 1, [])]

	assert unidad.verificar_capacidad(5, colaboradores=colaboradores) is True


def test_verificar_capacidad_devuelve_false_si_supera_el_limite_de_colaboradores():
	unidad = crear_unidad_trabajo(capacidad_colaboradores=2)
	colaboradores = [
		Colaborador("Ana", 1, []),
		Colaborador("Luis", 1, []),
		Colaborador("Pedro", 1, []),
	]

	assert unidad.verificar_capacidad(5, colaboradores=colaboradores) is False


def test_verificar_capacidad_rechaza_colaboradores_que_no_sean_lista():
	unidad = crear_unidad_trabajo()

	with pytest.raises(TipoInvalidoError, match="deben enviarse en una lista"):
		unidad.verificar_capacidad(5, colaboradores=(object(),))


def test_verificar_capacidad_rechaza_colaboradores_invalidos_y_repetidos():
	unidad = crear_unidad_trabajo()
	colaborador = Colaborador("Ana", 1, [])

	with pytest.raises(TipoInvalidoError):
		unidad.verificar_capacidad(5, colaboradores=[object()])

	with pytest.raises(ElementoDuplicadoError, match="repetidos"):
		unidad.verificar_capacidad(5, colaboradores=[colaborador, colaborador])


def test_verificar_capacidad_acepta_periodo_sin_solapamiento():
	unidad = crear_unidad_trabajo()
	unidad.asignar_periodo(crear_periodo(8, 10))

	assert unidad.verificar_capacidad(5, periodo=crear_periodo(10, 12)) is True


def test_verificar_capacidad_devuelve_false_si_el_periodo_se_solapa():
	unidad = crear_unidad_trabajo()
	unidad.asignar_periodo(crear_periodo(8, 10))

	assert unidad.verificar_capacidad(5, periodo=crear_periodo(9, 11)) is False
