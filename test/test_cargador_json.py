import copy
import json
from pathlib import Path

import pytest

from src.cargador_json import (
	cargar_sistema_desde_json,
	leer_configuracion,
)
from src.excepciones import ErrorConfiguracion


RUTA_CONFIGURACION_EJEMPLO = (
	Path(__file__).resolve().parents[1]
	/ "datos"
	/ "empresa.json"
)


@pytest.fixture
def configuracion():
	with RUTA_CONFIGURACION_EJEMPLO.open(encoding="utf-8") as archivo:
		return json.load(archivo)


def escribir_configuracion(tmp_path, configuracion):
	ruta = tmp_path / "configuracion.json"
	ruta.write_text(json.dumps(configuracion), encoding="utf-8")
	return ruta


def test_carga_y_programa_la_configuracion_de_ejemplo():
	sistema = cargar_sistema_desde_json(RUTA_CONFIGURACION_EJEMPLO)

	assert len(sistema.elementos_produccion) == 2
	assert len(sistema.colaboradores) == 1
	assert len(sistema.unidades_trabajo) == 1
	assert list(sistema.solicitudes) == ["SOL-1"]
	assert len(sistema.obtener_periodos_solicitud("SOL-1")) == 1


def test_rechaza_secciones_faltantes_y_campos_desconocidos(
	tmp_path,
	configuracion,
):
	configuracion_incompleta = copy.deepcopy(configuracion)
	del configuracion_incompleta["solicitudes"]

	with pytest.raises(ErrorConfiguracion, match="Falta la sección 'solicitudes'"):
		leer_configuracion(
			escribir_configuracion(tmp_path, configuracion_incompleta)
		)

	configuracion_desconocida = copy.deepcopy(configuracion)
	configuracion_desconocida["extra"] = True

	with pytest.raises(ErrorConfiguracion, match="Campos desconocidos"):
		leer_configuracion(
			escribir_configuracion(tmp_path, configuracion_desconocida)
		)


def test_rechaza_version_incompatible(tmp_path, configuracion):
	configuracion["version"] = 2

	with pytest.raises(ErrorConfiguracion, match="versión igual a 1"):
		cargar_sistema_desde_json(
			escribir_configuracion(tmp_path, configuracion)
		)


def test_rechaza_ids_de_elemento_duplicados(tmp_path, configuracion):
	configuracion["elementos"][1]["id"] = configuracion["elementos"][0]["id"]

	with pytest.raises(ErrorConfiguracion, match="ID de elemento duplicado"):
		cargar_sistema_desde_json(
			escribir_configuracion(tmp_path, configuracion)
		)


def test_rechaza_referencias_a_elementos_inexistentes(
	tmp_path,
	configuracion,
):
	configuracion["elementos"][1]["bom"][0]["elemento_id"] = "inexistente"

	with pytest.raises(ErrorConfiguracion, match="elemento inexistente"):
		cargar_sistema_desde_json(
			escribir_configuracion(tmp_path, configuracion)
		)


def test_rechaza_fechas_de_periodo_invalidas(tmp_path, configuracion):
	configuracion["solicitudes"][0]["periodos"][0]["inicio"] = "mañana"

	with pytest.raises(ErrorConfiguracion, match="fecha inválida"):
		cargar_sistema_desde_json(
			escribir_configuracion(tmp_path, configuracion)
		)


def test_rechaza_tarea_programada_antes_de_su_predecesora(
	tmp_path,
	configuracion,
):
	tareas = configuracion["procesos"][0]["tareas"]
	tareas[0]["tiempo"] = 1
	tareas[0]["predecesoras_ids"] = []
	tareas.append(
		{
			"id": "terminacion",
			"nombre": "Terminación",
			"tiempo": 1,
			"predecesoras_ids": ["armado"],
		}
	)
	configuracion["solicitudes"][0]["periodos"] = [
		{
			"tarea_id": "armado",
			"inicio": "2026-10-26T10:00:00",
			"fin": "2026-10-26T12:00:00",
		},
		{
			"tarea_id": "terminacion",
			"inicio": "2026-10-26T08:00:00",
			"fin": "2026-10-26T10:00:00",
		},
	]

	with pytest.raises(ErrorConfiguracion, match="no puede iniciar antes"):
		cargar_sistema_desde_json(
			escribir_configuracion(tmp_path, configuracion)
		)


def test_rechaza_solicitudes_con_recursos_programados_en_periodos_superpuestos(
	tmp_path,
	configuracion,
):
	segunda_solicitud = copy.deepcopy(configuracion["solicitudes"][0])
	segunda_solicitud["id"] = "SOL-2"
	configuracion["solicitudes"].append(segunda_solicitud)

	with pytest.raises(ErrorConfiguracion, match="período superpuesto"):
		cargar_sistema_desde_json(
			escribir_configuracion(tmp_path, configuracion)
		)
