import pytest
from datetime import datetime

from src.elementos import Producto
from src.excepciones import (
	ColaboradorNoDisponibleError,
	ElementoDuplicadoError,
	HabilidadRequeridaError,
	PeriodoOcupadoError,
	TipoInvalidoError,
)
from src.manufactura import (
	Colaborador,
	PeriodoOperacion,
	ProcesoManufactura,
	TareaDefinida,
	UnidadTrabajo,
)


def crear_producto():
	return Producto("Mesa", "unidad", 1)


def crear_tarea(nombre="Corte", costo=1, colaboradores=None, habilidades=None):
	return TareaDefinida(
		nombre,
		1,
		UnidadTrabajo(nombre, 10, costo, 2),
		colaboradores,
		habilidades,
	)


def crear_periodo(hora_inicio, hora_fin):
	return PeriodoOperacion(
		datetime(2026, 10, 9, hora_inicio),
		datetime(2026, 10, 9, hora_fin),
	)


def test_crear_proceso_manufactura_inicializa_producto_y_tareas():
	producto = crear_producto()

	proceso = ProcesoManufactura(producto)

	assert proceso.producto is producto
	assert proceso.tareas == []


def test_crear_proceso_manufactura_rechaza_producto_invalido():
	with pytest.raises(TipoInvalidoError, match="instancia de Producto"):
		ProcesoManufactura(object())


def test_agregar_tarea_agrega_y_devuelve_la_tarea():
	proceso = ProcesoManufactura(crear_producto())
	tarea = crear_tarea()

	resultado = proceso.agregar_tarea(tarea)

	assert resultado is tarea
	assert proceso.tareas == [tarea]


def test_agregar_tarea_rechaza_tarea_nula():
	proceso = ProcesoManufactura(crear_producto())

	with pytest.raises(TipoInvalidoError, match="instancia de TareaDefinida"):
		proceso.agregar_tarea(None)

	assert proceso.tareas == []


def test_agregar_tarea_rechaza_tarea_repetida():
	proceso = ProcesoManufactura(crear_producto())
	tarea = crear_tarea()
	proceso.agregar_tarea(tarea)

	with pytest.raises(ElementoDuplicadoError, match="tarea ya está agregada"):
		proceso.agregar_tarea(tarea)

	assert proceso.tareas == [tarea]


def test_modificar_proceso_reemplaza_la_lista_de_tareas():
	proceso = ProcesoManufactura(crear_producto())
	tareas = [crear_tarea("Corte"), crear_tarea("Pulido")]

	resultado = proceso.modificar_proceso(tareas)

	assert resultado == tareas
	assert proceso.tareas == tareas
	assert proceso.tareas is not tareas

	tareas.append(crear_tarea("Pintura"))
	assert len(proceso.tareas) == 2


def test_modificar_proceso_rechaza_un_valor_que_no_sea_lista():
	tarea_original = crear_tarea()
	proceso = ProcesoManufactura(crear_producto())
	proceso.agregar_tarea(tarea_original)

	with pytest.raises(TipoInvalidoError, match="Debe recibir una lista"):
		proceso.modificar_proceso((crear_tarea(),))

	assert proceso.tareas == [tarea_original]


def test_modificar_proceso_rechaza_tareas_invalidas_y_no_modifica_el_proceso():
	tarea_original = crear_tarea()
	proceso = ProcesoManufactura(crear_producto())
	proceso.agregar_tarea(tarea_original)

	with pytest.raises(TipoInvalidoError, match="lista de instancias"):
		proceso.modificar_proceso([crear_tarea(), object()])

	assert proceso.tareas == [tarea_original]


def test_modificar_proceso_rechaza_tareas_repetidas():
	proceso = ProcesoManufactura(crear_producto())
	tarea = crear_tarea()

	with pytest.raises(ElementoDuplicadoError, match="tareas repetidas"):
		proceso.modificar_proceso([tarea, tarea])

	assert proceso.tareas == []


def test_calcular_costo_operativo_suma_el_costo_de_todas_las_tareas():
	proceso = ProcesoManufactura(crear_producto())
	proceso.modificar_proceso(
		[crear_tarea("Corte", 125), crear_tarea("Pulido", 75), crear_tarea("Pintura", 1)]
	)

	assert proceso.calcular_costo_operativo() == 201


def test_calcular_costo_operativo_de_un_proceso_sin_tareas_es_cero():
	proceso = ProcesoManufactura(crear_producto())

	assert proceso.calcular_costo_operativo() == 0


def test_iniciar_proceso_valida_y_reserva_recursos_de_todas_las_tareas():
	colaborador = Colaborador("Ana", 50, ["soldadura"])
	unidad = UnidadTrabajo("Torno", 10, 300, 1)
	tarea = TareaDefinida("Corte", 2, unidad, [colaborador], ["soldadura"])
	proceso = ProcesoManufactura(crear_producto())
	proceso.agregar_tarea(tarea)
	periodo = crear_periodo(8, 10)

	resultado = proceso.iniciar_proceso(5, [periodo])

	assert len(resultado) == 1
	assert resultado[0].tarea_base is tarea
	assert resultado[0].estado == "pendiente"
	assert resultado[0].colaboradores == [colaborador]
	assert resultado[0].unidades_trabajo == [unidad]
	assert colaborador.periodos_ocupados == [periodo]
	assert unidad.periodos_ocupados == [periodo]


def test_iniciar_proceso_no_reserva_recursos_si_falla_una_tarea():
	colaborador = Colaborador("Ana", 50, ["soldadura"])
	unidad = UnidadTrabajo("Torno", 10, 300, 1)
	primera = TareaDefinida("Corte", 2, unidad, [colaborador], ["soldadura"])
	segunda = TareaDefinida("Pulido", 2, unidad, [colaborador], ["pintura"])
	proceso = ProcesoManufactura(crear_producto())
	proceso.modificar_proceso([primera, segunda])

	with pytest.raises(HabilidadRequeridaError):
		proceso.iniciar_proceso(5, [crear_periodo(8, 10), crear_periodo(10, 12)])

	assert colaborador.periodos_ocupados == []
	assert unidad.periodos_ocupados == []


def test_iniciar_proceso_acepta_subtarea_antes_de_su_tarea_padre():
	subtarea = crear_tarea("Preparación")
	tarea = crear_tarea("Corte")
	tarea.agregar_subtarea(subtarea)
	proceso = ProcesoManufactura(crear_producto())
	proceso.modificar_proceso([subtarea, tarea])

	resultado = proceso.iniciar_proceso(5, [crear_periodo(8, 9), crear_periodo(9, 10)])

	assert [tarea_en_curso.tarea_base for tarea_en_curso in resultado] == [subtarea, tarea]


def test_iniciar_proceso_rechaza_subtarea_ubicada_despues_del_padre():
	subtarea = crear_tarea("Preparación")
	tarea = crear_tarea("Corte")
	tarea.agregar_subtarea(subtarea)
	proceso = ProcesoManufactura(crear_producto())
	proceso.modificar_proceso([tarea, subtarea])

	with pytest.raises(TipoInvalidoError, match="deben preceder"):
		proceso.iniciar_proceso(5, [crear_periodo(8, 9), crear_periodo(9, 10)])

	assert subtarea.unidad_trabajo.periodos_ocupados == []
	assert tarea.unidad_trabajo.periodos_ocupados == []


def test_iniciar_proceso_rechaza_ciclos_de_subtareas():
	primera = crear_tarea("Primera")
	segunda = crear_tarea("Segunda")
	primera.agregar_subtarea(segunda)

	with pytest.raises(TipoInvalidoError, match="no pueden formar ciclos"):
		segunda.agregar_subtarea(primera)


def test_iniciar_proceso_rechaza_colaborador_repetido_en_periodos_superpuestos():
	colaborador = Colaborador("Ana", 50, ["soldadura"])
	primera = TareaDefinida(
		"Corte", 2, UnidadTrabajo("Torno 1", 10, 300, 1), [colaborador], ["soldadura"]
	)
	segunda = TareaDefinida(
		"Pulido", 2, UnidadTrabajo("Torno 2", 10, 300, 1), [colaborador], ["soldadura"]
	)
	proceso = ProcesoManufactura(crear_producto())
	proceso.modificar_proceso([primera, segunda])

	with pytest.raises(ColaboradorNoDisponibleError, match="reserva superpuesta"):
		proceso.iniciar_proceso(5, [crear_periodo(8, 10), crear_periodo(9, 11)])

	assert colaborador.periodos_ocupados == []


def test_iniciar_proceso_rechaza_unidad_repetida_en_periodos_superpuestos():
	unidad = UnidadTrabajo("Torno", 10, 300, 0)
	primera = TareaDefinida("Corte", 2, unidad, [], [])
	segunda = TareaDefinida("Pulido", 2, unidad, [], [])
	proceso = ProcesoManufactura(crear_producto())
	proceso.modificar_proceso([primera, segunda])

	with pytest.raises(PeriodoOcupadoError, match="reserva superpuesta"):
		proceso.iniciar_proceso(5, [crear_periodo(8, 10), crear_periodo(9, 11)])

	assert unidad.periodos_ocupados == []
