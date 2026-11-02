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
    return {
        "version": 3,
        "elementos": [
            {
                "id": "madera",
                "tipo": "insumo",
                "nombre": "Madera",
                "unidad_medida": "m2",
                "costo": 50,
            },
            {
                "id": "mesa",
                "tipo": "producto",
                "nombre": "Mesa",
                "unidad_medida": "unidad",
                "costo": 1,
                "bom": [
                    {
                        "elemento_id": "madera",
                        "cantidad": 2,
                    }
                ],
            },
        ],
        "colaboradores": [
            {
                "id": "ana",
                "nombre": "Ana",
                "costo_por_hora": 25,
                "habilidades": ["armado"],
            }
        ],
        "unidades_trabajo": [
            {
                "id": "banco",
                "nombre": "Banco",
                "capacidad_max_produccion": 10,
                "costo_fijo": 30,
                "capacidad_colaboradores": 1,
            }
        ],
        "procesos": [
            {
                "id": "proceso_mesa",
				"producto_id": "mesa",
                "tareas": [
                    {
                        "id": "armado",
                        "nombre": "Armado de mesa",
                        "tiempo": 1,
                        "unidad_trabajo_id": "banco",
                        "colaboradores_ids": ["ana"],
                        "habilidades_requeridas": ["armado"],
                    }
                ],
            }
        ],
    }

def escribir_configuracion(tmp_path, configuracion):
	ruta = tmp_path / "configuracion.json"
	ruta.write_text(json.dumps(configuracion), encoding="utf-8")
	return ruta


def test_carga_solo_configuracion_estatica(
    tmp_path,
    configuracion,
):
    ruta = escribir_configuracion(tmp_path, configuracion)
    sistema = cargar_sistema_desde_json(ruta)

    assert set(sistema.elementos_produccion) == {"Madera", "Mesa"}
    assert len(sistema.colaboradores) == 1
    assert len(sistema.unidades_trabajo) == 1
    assert sistema.solicitudes == {}
    assert sistema.inventario.obtener_stock(
        sistema.elementos_produccion["Mesa"]
    ) == {"actual": 0, "reservado": 0}


def test_rechaza_secciones_faltantes_y_campos_desconocidos(
	tmp_path,
	configuracion,
):
	configuracion_incompleta = copy.deepcopy(configuracion)
	del configuracion_incompleta["procesos"]

	with pytest.raises(ErrorConfiguracion, match="Falta la sección 'procesos'"):
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
	configuracion["version"] = 4

	with pytest.raises(ErrorConfiguracion, match="versión igual a 3"):
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


def test_rechaza_solicitudes_en_configuracion_estatica(tmp_path, configuracion):
	configuracion["solicitudes"] = []

	with pytest.raises(ErrorConfiguracion, match="Campos desconocidos"):
		cargar_sistema_desde_json(
			escribir_configuracion(tmp_path, configuracion)
		)


def test_programa_tarea_despues_de_su_predecesora(
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
	sistema = cargar_sistema_desde_json(
		escribir_configuracion(tmp_path, configuracion)
	)
	assert sistema.crear_orden_fabricacion(
		"SOL-1", sistema.elementos_produccion["Mesa"], 1
	)
	sistema.inventario.agregar_stock(
		sistema.elementos_produccion["Madera"], 2
	)
	assert sistema.procesar_siguiente_solicitud()
	periodos = sistema.obtener_programacion_produccion("SOL-1")[
		sistema.elementos_produccion["Mesa"]
	]
	assert periodos[1].inicio >= periodos[0].fin
