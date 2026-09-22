import pytest

from src.manufactura import Colaborador, TareaDefinida, UnidadTrabajo


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

	with pytest.raises(ValueError, match="no puede ser nula"):
		tarea.agregar_subtarea(None)

	assert tarea.subtareas == []


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

	with pytest.raises(TypeError, match="deben enviarse en una lista"):
		tarea.validar_habilidades(None)


def test_cantidad_colaboradores_suficiente_compara_con_los_requeridos():
	colaboradores_requeridos = [Colaborador("Ana", 50, []), Colaborador("Luis", 40, [])]
	tarea = crear_tarea(colaboradores_requeridos=colaboradores_requeridos)

	assert tarea.cantidad_colaboradores_suficiente([object(), object()]) is True
	assert tarea.cantidad_colaboradores_suficiente([object()]) is False


def test_cantidad_colaboradores_suficiente_rechaza_un_valor_que_no_sea_lista():
	tarea = crear_tarea()

	with pytest.raises(TypeError, match="deben enviarse en una lista"):
		tarea.cantidad_colaboradores_suficiente(None)


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


def test_costo_operativo_es_cero_si_no_hay_unidad_de_trabajo():
	colaborador = Colaborador("Ana", 50, [])
	tarea = crear_tarea(
		tiempo=2,
		colaboradores_requeridos=[colaborador],
	)

	assert tarea.costo_operativo() == 0
