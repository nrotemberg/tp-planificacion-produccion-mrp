from datetime import datetime

import pytest

from src.manufactura import Colaborador, PeriodoOperacion
from src.excepciones import TipoInvalidoError


def crear_colaborador(nombre="Ana", costo_por_hora=50, habilidades=None):
	return Colaborador(nombre, costo_por_hora, habilidades)


def crear_periodo(hora_inicio, hora_fin):
	return PeriodoOperacion(
		datetime(2026, 9, 22, hora_inicio),
		datetime(2026, 9, 22, hora_fin),
	)


def test_crear_colaborador_inicializa_sus_atributos():
	colaborador = crear_colaborador(habilidades=["soldadura", "pintura"])

	assert colaborador.nombre == "Ana"
	assert colaborador.costo_por_hora == 50
	assert colaborador.habilidades == ["soldadura", "pintura"]
	assert colaborador.periodos_ocupados == []


def test_habilidades_nulas_se_inicializan_vacias():
	colaborador = crear_colaborador(habilidades=None)

	assert colaborador.habilidades == []


@pytest.mark.parametrize("habilidad", ["soldadura", "pintura"])
def test_tiene_habilidad_devuelve_true_para_habilidades_registradas(habilidad):
	colaborador = crear_colaborador(habilidades=["soldadura", "pintura"])

	assert colaborador.tiene_habilidad(habilidad) is True


def test_tiene_habilidad_devuelve_false_para_habilidad_no_registrada():
	colaborador = crear_colaborador(habilidades=["soldadura"])

	assert colaborador.tiene_habilidad("mecanizado") is False


def test_asignar_periodo_agrega_un_periodo_valido():
	colaborador = crear_colaborador()
	periodo = crear_periodo(8, 10)

	colaborador.asignar_periodo(periodo)

	assert colaborador.periodos_ocupados == [periodo]


def test_asignar_periodo_rechaza_un_valor_invalido():
	colaborador = crear_colaborador()

	with pytest.raises(TipoInvalidoError, match="Debe asignarse un PeriodoOperacion"):
		colaborador.asignar_periodo("08:00-10:00")

	assert colaborador.periodos_ocupados == []


def test_verificar_disponibilidad_es_true_sin_periodos_ocupados():
	colaborador = crear_colaborador()

	assert colaborador.verificar_disponibilidad(crear_periodo(8, 10)) is True


def test_verificar_disponibilidad_es_true_si_no_hay_solapamiento():
	colaborador = crear_colaborador()
	colaborador.asignar_periodo(crear_periodo(8, 10))

	assert colaborador.verificar_disponibilidad(crear_periodo(10, 12)) is True


def test_verificar_disponibilidad_es_false_si_hay_solapamiento():
	colaborador = crear_colaborador()
	colaborador.asignar_periodo(crear_periodo(8, 10))

	assert colaborador.verificar_disponibilidad(crear_periodo(9, 11)) is False


def test_verificar_disponibilidad_rechaza_un_valor_invalido():
	colaborador = crear_colaborador()

	with pytest.raises(TipoInvalidoError, match="Debe verificarse con un PeriodoOperacion"):
		colaborador.verificar_disponibilidad(None)
