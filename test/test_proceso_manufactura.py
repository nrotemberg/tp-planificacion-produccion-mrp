import pytest

from src.manufactura import ProcesoManufactura


class TareaConCosto:
	def __init__(self, costo):
		self.costo = costo

	def costo_operativo(self):
		return self.costo


def test_crear_proceso_manufactura_inicializa_producto_y_tareas():
	producto = object()

	proceso = ProcesoManufactura(producto)

	assert proceso.producto is producto
	assert proceso.tareas == []


def test_agregar_tarea_agrega_y_devuelve_la_tarea():
	proceso = ProcesoManufactura(object())
	tarea = object()

	resultado = proceso.agregar_tarea(tarea)

	assert resultado is tarea
	assert proceso.tareas == [tarea]


def test_agregar_tarea_rechaza_tarea_nula():
	proceso = ProcesoManufactura(object())

	with pytest.raises(ValueError, match="no puede ser nula"):
		proceso.agregar_tarea(None)

	assert proceso.tareas == []


def test_agregar_proceso_funciona_como_alias_de_agregar_tarea():
	proceso = ProcesoManufactura(object())
	tarea = object()

	assert proceso.agregar_proceso(tarea) is tarea
	assert proceso.tareas == [tarea]


def test_modificar_proceso_reemplaza_la_lista_de_tareas():
	proceso = ProcesoManufactura(object())
	tareas = [object(), object()]

	resultado = proceso.modificar_proceso(tareas)

	assert resultado is tareas
	assert proceso.tareas is tareas


def test_modificar_proceso_rechaza_un_valor_que_no_sea_lista():
	tarea_original = object()
	proceso = ProcesoManufactura(object())
	proceso.agregar_tarea(tarea_original)

	with pytest.raises(TypeError, match="Debe recibir una lista"):
		proceso.modificar_proceso((object(),))

	assert proceso.tareas == [tarea_original]


def test_calcular_costo_operativo_suma_el_costo_de_todas_las_tareas():
	proceso = ProcesoManufactura(object())
	proceso.modificar_proceso(
		[TareaConCosto(125), TareaConCosto(75), TareaConCosto(0)]
	)

	assert proceso.calcular_costo_operativo() == 200


def test_calcular_costo_operativo_de_un_proceso_sin_tareas_es_cero():
	proceso = ProcesoManufactura(object())

	assert proceso.calcular_costo_operativo() == 0
