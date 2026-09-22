import pytest

from src.manufactura import TareaEnCurso
from src.excepciones import EstadoSolicitudError, TipoInvalidoError


def crear_tarea_en_curso(nombre="Corte", tarea_base=None, estado="pendiente"):
	return TareaEnCurso(nombre, tarea_base, estado)


def test_crear_tarea_en_curso_inicializa_sus_atributos():
	tarea_base = object()

	tarea = crear_tarea_en_curso(tarea_base=tarea_base)

	assert tarea.nombre == "Corte"
	assert tarea.tarea_base is tarea_base
	assert tarea.estado == "pendiente"
	assert tarea.colaboradores == []
	assert tarea.unidades_trabajo == []
	assert tarea.historial_estados == ["pendiente"]


@pytest.mark.parametrize(
	"nuevo_estado",
	["pendiente", "en_curso", "pausada", "finalizada", "cancelada"],
)
def test_actualizar_estado_acepta_estados_validos(nuevo_estado):
	tarea = crear_tarea_en_curso()

	tarea.actualizar_estado(nuevo_estado)

	assert tarea.estado == nuevo_estado
	assert tarea.historial_estados == ["pendiente", nuevo_estado]


def test_actualizar_estado_registra_toda_la_evolucion():
	tarea = crear_tarea_en_curso()

	tarea.actualizar_estado("en_curso")
	tarea.actualizar_estado("pausada")
	tarea.actualizar_estado("finalizada")

	assert tarea.estado == "finalizada"
	assert tarea.historial_estados == [
		"pendiente",
		"en_curso",
		"pausada",
		"finalizada",
	]


def test_actualizar_estado_rechaza_un_estado_invalido():
	tarea = crear_tarea_en_curso()

	with pytest.raises(EstadoSolicitudError, match="Estado no válido"):
		tarea.actualizar_estado("desconocido")

	assert tarea.estado == "pendiente"
	assert tarea.historial_estados == ["pendiente"]


def test_asignar_colaboradores_guarda_la_lista_recibida():
	tarea = crear_tarea_en_curso()
	colaboradores = [object(), object()]

	tarea.asignar_colaboradores(colaboradores)

	assert tarea.colaboradores is colaboradores


def test_asignar_colaboradores_rechaza_un_valor_que_no_sea_lista():
	tarea = crear_tarea_en_curso()

	with pytest.raises(TipoInvalidoError, match="deben enviarse en una lista"):
		tarea.asignar_colaboradores(None)

	assert tarea.colaboradores == []


def test_asignar_unidades_de_trabajo_guarda_la_lista_recibida():
	tarea = crear_tarea_en_curso()
	unidades = [object(), object()]

	tarea.asignar_UTs(unidades)

	assert tarea.unidades_trabajo is unidades


def test_asignar_unidades_de_trabajo_rechaza_un_valor_que_no_sea_lista():
	tarea = crear_tarea_en_curso()

	with pytest.raises(TipoInvalidoError, match="deben enviarse en una lista"):
		tarea.asignar_UTs(None)

	assert tarea.unidades_trabajo == []
