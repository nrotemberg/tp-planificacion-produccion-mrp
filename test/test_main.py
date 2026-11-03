from pathlib import Path

from src.cargador_json import cargar_sistema_desde_json
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
