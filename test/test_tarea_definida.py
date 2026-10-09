import pytest

from src.manufactura import Colaborador, TareaDefinida, UnidadTrabajo
from src.excepciones import (
	CantidadInvalidaError,
	CostoInvalidoError,
	ElementoDuplicadoError,
	TipoInvalidoError,
)


def crear_tarea(
	nombre="Corte",
	tiempo=2,
	unidad_trabajo=None,
	colaboradores_requeridos=None,
	habilidades_requeridas=None,
):
	return TareaDefinida(
		nombre,
		tiempo,
		unidad_trabajo,
		colaboradores_requeridos,
		habilidades_requeridas,
	)


def test_crear_tarea_definida_inicializa_sus_atributos():
	unidad = UnidadTrabajo("Torno", 100, 300, 2)
	colaborador = Colaborador("Ana", 50, ["soldadura"])

	tarea = crear_tarea(
		tiempo=3,
		unidad_trabajo=unidad,
		colaboradores_requeridos=[colaborador],
		habilidades_requeridas=["soldadura"],
	)

	assert tarea.nombre == "Corte"
	assert tarea.tiempo == 3
	assert tarea.unidad_trabajo is unidad
	assert tarea.colaboradores_requeridos == [colaborador]
	assert tarea.habilidades_requeridas == ["soldadura"]
	assert tarea.subtareas == []


def test_listas_nulas_se_inicializan_vacias():
	tarea = crear_tarea(colaboradores_requeridos=None, habilidades_requeridas=None)

	assert tarea.colaboradores_requeridos == []
	assert tarea.habilidades_requeridas == []


def test_agregar_subtarea_agrega_y_devuelve_la_subtarea():
	tarea = crear_tarea()
	subtarea = crear_tarea(nombre="Pulido")

	resultado = tarea.agregar_subtarea(subtarea)

	assert resultado is subtarea
	assert tarea.subtareas == [subtarea]


def test_agregar_subtarea_rechaza_valor_nulo():
	tarea = crear_tarea()

	with pytest.raises(TipoInvalidoError, match="instancia de TareaDefinida"):
		tarea.agregar_subtarea(None)

	assert tarea.subtareas == []


def test_agregar_subtarea_rechaza_tipo_invalido():
	tarea = crear_tarea()

	with pytest.raises(TipoInvalidoError, match="instancia de TareaDefinida"):
		tarea.agregar_subtarea(object())

	assert tarea.subtareas == []


def test_agregar_subtarea_rechaza_la_propia_tarea():
	tarea = crear_tarea()

	with pytest.raises(TipoInvalidoError, match="no pueden formar ciclos"):
		tarea.agregar_subtarea(tarea)

	assert tarea.subtareas == []


def test_agregar_subtarea_rechaza_subtarea_repetida():
	tarea = crear_tarea()
	subtarea = crear_tarea(nombre="Pulido")
	tarea.agregar_subtarea(subtarea)

	with pytest.raises(ElementoDuplicadoError, match="ya está agregada"):
		tarea.agregar_subtarea(subtarea)

	assert tarea.subtareas == [subtarea]


def test_agregar_subtarea_rechaza_ciclo_indirecto():
	primera = crear_tarea("Primera")
	segunda = crear_tarea("Segunda")
	tercera = crear_tarea("Tercera")
	primera.agregar_subtarea(segunda)
	segunda.agregar_subtarea(tercera)

	with pytest.raises(TipoInvalidoError, match="no pueden formar ciclos"):
		tercera.agregar_subtarea(primera)

	assert tercera.subtareas == []


@pytest.mark.parametrize(
	"parametros, excepcion, mensaje",
	[
		(("", 2, None, None, None), TipoInvalidoError, "nombre"),
		(("Corte", "dos", None, None, None), TipoInvalidoError, "tiempo"),
		(("Corte", 0, None, None, None), CantidadInvalidaError, "mayor que cero"),
		(("Corte", 2, object(), None, None), TipoInvalidoError, "UnidadTrabajo"),
		(("Corte", 2, None, (object(),), None), TipoInvalidoError, "colaboradores"),
		(("Corte", 2, None, [object()], None), TipoInvalidoError, "Colaborador"),
		(("Corte", 2, None, None, ("soldadura",)), TipoInvalidoError, "habilidades"),
		(("Corte", 2, None, None, [""]), TipoInvalidoError, "textos no vacíos"),
	],
)
def test_constructor_rechaza_parametros_invalidos(parametros, excepcion, mensaje):
	with pytest.raises(excepcion, match=mensaje):
		TareaDefinida(*parametros)


def test_validar_habilidades_devuelve_true_si_estan_cubiertas():
	colaborador = Colaborador("Ana", 50, ["soldadura", "pintura"])
	tarea = crear_tarea(habilidades_requeridas=["soldadura", "pintura"])

	assert tarea.validar_habilidades([colaborador]) is True


def test_validar_habilidades_devuelve_false_si_falta_una_habilidad():
	colaborador = Colaborador("Ana", 50, ["soldadura"])
	tarea = crear_tarea(habilidades_requeridas=["soldadura", "pintura"])

	assert tarea.validar_habilidades([colaborador]) is False


def test_validar_habilidades_sin_requisitos_devuelve_true():
	tarea = crear_tarea(habilidades_requeridas=[])

	assert tarea.validar_habilidades([]) is True


def test_validar_habilidades_rechaza_un_valor_que_no_sea_lista():
	tarea = crear_tarea()

	with pytest.raises(TipoInvalidoError, match="deben enviarse en una lista"):
		tarea.validar_habilidades(None)


def test_validar_habilidades_rechaza_colaborador_invalido():
	tarea = crear_tarea(habilidades_requeridas=["soldadura"])

	with pytest.raises(TipoInvalidoError, match="Todos los colaboradores"):
		tarea.validar_habilidades([object()])


def test_cantidad_colaboradores_suficiente_compara_con_los_requeridos():
	colaboradores_requeridos = [Colaborador("Ana", 50, []), Colaborador("Luis", 40, [])]
	tarea = crear_tarea(colaboradores_requeridos=colaboradores_requeridos)
	colaboradores_disponibles = [Colaborador("Pedro", 30, []), Colaborador("Sofía", 35, [])]

	assert tarea.cantidad_colaboradores_suficiente(colaboradores_disponibles) is True
	assert tarea.cantidad_colaboradores_suficiente([colaboradores_disponibles[0]]) is False


def test_cantidad_colaboradores_suficiente_rechaza_un_valor_que_no_sea_lista():
	tarea = crear_tarea()

	with pytest.raises(TipoInvalidoError, match="deben enviarse en una lista"):
		tarea.cantidad_colaboradores_suficiente(None)


def test_cantidad_colaboradores_suficiente_rechaza_colaboradores_repetidos():
	colaborador = Colaborador("Ana", 50, [])
	tarea = crear_tarea(colaboradores_requeridos=[colaborador])

	with pytest.raises(ElementoDuplicadoError, match="colaboradores repetidos"):
		tarea.cantidad_colaboradores_suficiente([colaborador, colaborador])


def test_costo_operativo_suma_costo_fijo_y_colaboradores():
	unidad = UnidadTrabajo("Torno", 100, 300, 2)
	colaboradores = [
		Colaborador("Ana", 50, []),
		Colaborador("Luis", 25, []),
	]
	tarea = crear_tarea(
		tiempo=2,
		unidad_trabajo=unidad,
		colaboradores_requeridos=colaboradores,
	)

	assert tarea.costo_operativo() == 450


def test_costo_operativo_suma_colaboradores_sin_unidad_de_trabajo():
	colaborador = Colaborador("Ana", 50, [])
	tarea = crear_tarea(
		tiempo=2,
		colaboradores_requeridos=[colaborador],
	)

	assert tarea.costo_operativo() == 100


def test_costo_operativo_rechaza_costo_fijo_negativo():
	with pytest.raises(CostoInvalidoError, match="costo fijo"):
		UnidadTrabajo("Torno", 100, -1, 2)


def test_costo_operativo_rechaza_costo_horario_negativo():
	with pytest.raises(CostoInvalidoError, match="costo por hora"):
		Colaborador("Ana", -1, [])
