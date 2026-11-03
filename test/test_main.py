import json
import shutil
import sys
from pathlib import Path

import pytest

from main import main as ejecutar_main
from src.cargador_json import cargar_sistema_desde_json
from src.elementos import Insumo
from src.excepciones import RecursosInsuficientesError
from src.persistencia_json import cargar_estado, guardar_estado
from main import (
    _productos_fabricables,
    crear_solicitud,
    mostrar_cuellos_de_botella,
    mostrar_colaboradores,
    mostrar_historial_tareas,
    mostrar_tareas_cargadas,
    mostrar_unidades_trabajo,
)


RUTA_CONFIGURACION_EJEMPLO = (
    Path(__file__).resolve().parents[1]
    / "datos"
    / "empresa.json"
)


def test_muestra_todos_los_productos_fabricables_incluidos_subproductos():
    sistema = cargar_sistema_desde_json(RUTA_CONFIGURACION_EJEMPLO)

    assert [
        producto.nombre
        for producto in _productos_fabricables(sistema)
    ] == ["Pata", "Tabla", "Mesa"]


def test_crear_solicitud_permite_elegir_un_subproducto(
    monkeypatch,
    capsys,
):
    sistema = cargar_sistema_desde_json(RUTA_CONFIGURACION_EJEMPLO)
    respuestas = iter(("1", "2", ""))
    monkeypatch.setattr("builtins.input", lambda _: next(respuestas))

    crear_solicitud(sistema)

    salida = capsys.readouterr().out
    assert "1. Pata" in salida
    assert "2. Tabla" in salida
    assert "3. Mesa" in salida
    solicitud = sistema.obtener_solicitud_por_id("SOL-1")
    assert solicitud.producto.nombre == "Pata"
    assert solicitud.inicio_planificacion is None


def test_no_crea_solicitud_si_cantidad_supera_capacidad_de_ut(
    monkeypatch,
):
    sistema = cargar_sistema_desde_json(RUTA_CONFIGURACION_EJEMPLO)
    respuestas = iter(("3", "12", ""))
    monkeypatch.setattr("builtins.input", lambda _: next(respuestas))

    with pytest.raises(RecursosInsuficientesError, match="capacidad máxima"):
        crear_solicitud(sistema)

    assert sistema.solicitudes == {}


def test_carga_stock_guardado_en_estado(tmp_path):
    sistema = cargar_sistema_desde_json(RUTA_CONFIGURACION_EJEMPLO)
    madera = sistema.elementos_produccion["Madera"]
    tornillos = sistema.elementos_produccion["Tornillos"]
    sistema.inventario.agregar_stock(madera, 17)
    sistema.inventario.agregar_stock(tornillos, 23)
    ruta_estado = tmp_path / "empresa_estado.json"
    guardar_estado(ruta_estado, sistema)

    sistema_restaurado = cargar_sistema_desde_json(RUTA_CONFIGURACION_EJEMPLO)
    assert cargar_estado(ruta_estado, sistema_restaurado)
    assert sistema_restaurado.inventario.obtener_stock(
        sistema_restaurado.elementos_produccion["Madera"]
    ) == {"actual": 17, "reservado": 0}
    assert sistema_restaurado.inventario.obtener_stock(
        sistema_restaurado.elementos_produccion["Tornillos"]
    ) == {"actual": 23, "reservado": 0}


def test_mostrar_cuellos_de_botella_imprime_las_unidades_mas_cargadas(
    capsys,
):
    sistema = cargar_sistema_desde_json(RUTA_CONFIGURACION_EJEMPLO)

    mostrar_cuellos_de_botella(sistema)

    salida = capsys.readouterr().out
    assert "Cuellos de botella" in salida
    assert "No hay unidades de trabajo ocupadas." in salida


def test_cuellos_de_botella_acumula_horas_fabricadas_por_ut():
    sistema = cargar_sistema_desde_json(RUTA_CONFIGURACION_EJEMPLO)
    for elemento in sistema.elementos_produccion.values():
        if isinstance(elemento, Insumo):
            sistema.inventario.agregar_stock(elemento, 100)

    assert sistema.crear_orden_fabricacion(
        "SOL-1",
        sistema.elementos_produccion["Mesa"],
        1,
    )
    assert sistema.procesar_siguiente_solicitud()
    assert sistema.detectar_cuello() == []

    sistema.iniciar_produccion("SOL-1")
    while sistema.fabricar_siguiente_producto("SOL-1") is not None:
        pass

    carga_por_unidad = {
        carga["unidad"].nombre: carga["horas_ocupadas"]
        for carga in sistema.detectar_cuello()
    }
    assert carga_por_unidad == {"Sierra": 2, "Banco de ensamblaje": 0.5}


def test_mostrar_historial_tareas_informa_si_no_hay_tareas_en_la_sesion(
    capsys,
):
    sistema = cargar_sistema_desde_json(RUTA_CONFIGURACION_EJEMPLO)

    mostrar_historial_tareas(sistema)

    salida = capsys.readouterr().out
    assert "Historial de tareas" in salida
    assert "No hay tareas ejecutadas en esta sesión." in salida


def test_mostrar_tareas_cargadas_imprime_informacion_relevante(capsys):
    sistema = cargar_sistema_desde_json(RUTA_CONFIGURACION_EJEMPLO)

    mostrar_tareas_cargadas(sistema)

    salida = capsys.readouterr().out
    assert "Tareas cargadas" in salida
    assert "Fabricar pata" in salida
    assert "Producto: Pata" in salida
    assert "Tiempo:" in salida


def test_mostrar_unidades_y_colaboradores_cargados(capsys):
    sistema = cargar_sistema_desde_json(RUTA_CONFIGURACION_EJEMPLO)

    mostrar_unidades_trabajo(sistema)
    mostrar_colaboradores(sistema)

    salida = capsys.readouterr().out
    assert "Unidades de trabajo" in salida
    assert "Sierra" in salida
    assert "Capacidad máxima:" in salida
    assert "Colaboradores" in salida
    assert "Ana" in salida
    assert "Habilidades:" in salida


def test_main_recorrido_interactivo_completo(tmp_path, monkeypatch, capsys):
    ruta_configuracion = tmp_path / "empresa_demo.json"
    shutil.copyfile(RUTA_CONFIGURACION_EJEMPLO, ruta_configuracion)
    monkeypatch.setattr(
        sys,
        "argv",
        ["main.py", str(ruta_configuracion)],
    )
    respuestas = iter(
        (
            "4",
            "5",
            "3",
            "1",
            "Presentación",
            "2",
            "1",
            "3",
            "6",
            "7",
            "8",
            "9",
            "10",
            "99",
            "11",
        )
    )
    monkeypatch.setattr("builtins.input", lambda _: next(respuestas))
    pausas = []
    monkeypatch.setattr("main.sleep", pausas.append)

    assert ejecutar_main() == 0
    assert pausas == [5, 5, 5]

    salida = capsys.readouterr().out
    assert "Configuración cargada:" in salida
    assert "Se agregaron 100 unidades a Madera." in salida
    assert "Solicitud SOL-1 creada." in salida
    assert "SOL-1: Mesa x 1 | creada | Presentación" in salida
    assert "Procesando SOL-1: Mesa x 1" in salida
    assert "Fabricado: Pata | Cantidad: 4" in salida
    assert "Fabricado: Tabla | Cantidad: 1" in salida
    assert "Fabricado: Mesa | Cantidad: 1" in salida
    assert "Estado: finalizada (pedido entregado a Presentación)" in salida
    assert "Inventario" in salida
    assert "Cuellos de botella" in salida
    assert "Historial de tareas" in salida
    assert "Tareas cargadas" in salida
    assert "Unidades de trabajo" in salida
    assert "Colaboradores" in salida
    assert "Opción inválida. Elegí un número del 1 al 11." in salida
    assert "Saliendo del sistema." in salida

    estado = json.loads(
        (tmp_path / "empresa_demo_estado.json").read_text(encoding="utf-8")
    )
    assert estado["solicitudes"][0]["estado"] == "finalizada"
    assert estado["cola"] == []
