from datetime import datetime, timedelta

import pytest

from src.manufactura import PeriodoOperacion


def crear_datetime(hora, minuto=0):
	return datetime(2026, 9, 22, hora, minuto)


def test_crear_periodo_operacion_inicializa_inicio_y_fin():
	inicio = crear_datetime(8)
	fin = crear_datetime(10)

	periodo = PeriodoOperacion(inicio, fin)

	assert periodo.inicio == inicio
	assert periodo.fin == fin


def test_crear_periodo_rechaza_inicio_que_no_sea_datetime():
	with pytest.raises(TypeError, match="Inicio y fin deben ser datetime"):
		PeriodoOperacion("08:00", crear_datetime(10))


def test_crear_periodo_rechaza_fin_que_no_sea_datetime():
	with pytest.raises(TypeError, match="Inicio y fin deben ser datetime"):
		PeriodoOperacion(crear_datetime(8), "10:00")


@pytest.mark.parametrize(
	"inicio, fin",
	[
		(crear_datetime(8), crear_datetime(8)),
		(crear_datetime(10), crear_datetime(8)),
	],
)
def test_crear_periodo_rechaza_fin_igual_o_anterior_al_inicio(inicio, fin):
	with pytest.raises(ValueError, match="fecha fin debe ser posterior"):
		PeriodoOperacion(inicio, fin)

def test_duracion_horas_devuelve_la_duracion_completa():
	periodo = PeriodoOperacion(crear_datetime(8, 30), crear_datetime(11))

	assert periodo.duracion_horas() == 2.5


def test_duracion_horas_funciona_con_dias_diferentes():
	inicio = crear_datetime(23)
	fin = inicio + timedelta(hours=2)
	periodo = PeriodoOperacion(inicio, fin)

	assert periodo.duracion_horas() == 2


def test_se_solapa_con_devuelve_true_para_periodos_superpuestos():
	periodo = PeriodoOperacion(crear_datetime(8), crear_datetime(10))
	otro = PeriodoOperacion(crear_datetime(9), crear_datetime(11))

	assert periodo.se_solapa_con(otro) is True
	assert otro.se_solapa_con(periodo) is True


def test_se_solapa_con_devuelve_false_para_periodos_contiguos():
	periodo = PeriodoOperacion(crear_datetime(8), crear_datetime(10))
	otro = PeriodoOperacion(crear_datetime(10), crear_datetime(12))

	assert periodo.se_solapa_con(otro) is False


def test_se_solapa_con_devuelve_false_para_periodos_separados():
	periodo = PeriodoOperacion(crear_datetime(8), crear_datetime(10))
	otro = PeriodoOperacion(crear_datetime(12), crear_datetime(14))

	assert periodo.se_solapa_con(otro) is False


def test_se_solapa_con_rechaza_un_valor_que_no_sea_periodo():
	periodo = PeriodoOperacion(crear_datetime(8), crear_datetime(10))

	with pytest.raises(TypeError, match="Debe compararse con otro PeriodoOperacion"):
		periodo.se_solapa_con(None)
