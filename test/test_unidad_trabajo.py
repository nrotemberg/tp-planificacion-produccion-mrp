from datetime import datetime

import pytest

from src.manufactura import PeriodoOperacion, UnidadTrabajo


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


def test_asignar_periodo_agrega_un_periodo_valido():
	unidad = crear_unidad_trabajo()
	periodo = crear_periodo(8, 10)

	unidad.asignar_periodo(periodo)

	assert unidad.periodos_ocupados == [periodo]


def test_asignar_periodo_rechaza_un_valor_invalido():
	unidad = crear_unidad_trabajo()

	with pytest.raises(TypeError, match="Debe asignarse un PeriodoOperacion"):
		unidad.asignar_periodo("08:00-10:00")

	assert unidad.periodos_ocupados == []


def test_verificar_capacidad_acepta_cantidad_dentro_del_limite():
	unidad = crear_unidad_trabajo()

	assert unidad.verificar_capacidad(10) is True


@pytest.mark.parametrize("cantidad", [0, -1])
def test_verificar_capacidad_rechaza_cantidades_no_positivas(cantidad):
	unidad = crear_unidad_trabajo()

	with pytest.raises(ValueError, match="debe ser mayor que cero"):
		unidad.verificar_capacidad(cantidad)


def test_verificar_capacidad_devuelve_false_si_supera_la_produccion_maxima():
	unidad = crear_unidad_trabajo(capacidad_max_produccion=10)

	assert unidad.verificar_capacidad(11) is False


def test_verificar_capacidad_acepta_colaboradores_dentro_del_limite():
	unidad = crear_unidad_trabajo(capacidad_colaboradores=2)

	assert unidad.verificar_capacidad(5, colaboradores=[object(), object()]) is True


def test_verificar_capacidad_devuelve_false_si_supera_el_limite_de_colaboradores():
	unidad = crear_unidad_trabajo(capacidad_colaboradores=2)

	assert unidad.verificar_capacidad(5, colaboradores=[object(), object(), object()]) is False


def test_verificar_capacidad_rechaza_colaboradores_que_no_sean_lista():
	unidad = crear_unidad_trabajo()

	with pytest.raises(TypeError, match="deben enviarse en una lista"):
		unidad.verificar_capacidad(5, colaboradores=(object(),))


def test_verificar_capacidad_acepta_periodo_sin_solapamiento():
	unidad = crear_unidad_trabajo()
	unidad.asignar_periodo(crear_periodo(8, 10))

	assert unidad.verificar_capacidad(5, periodo=crear_periodo(10, 12)) is True


def test_verificar_capacidad_devuelve_false_si_el_periodo_se_solapa():
	unidad = crear_unidad_trabajo()
	unidad.asignar_periodo(crear_periodo(8, 10))

	assert unidad.verificar_capacidad(5, periodo=crear_periodo(9, 11)) is False
