from pathlib import Path

from src.cargador_json import cargar_sistema_desde_json
from src.persistencia_json import cargar_estado
from main import _productos_fabricables, crear_solicitud


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


def test_estado_inicial_no_carga_stock_de_ejemplo():
    sistema = cargar_sistema_desde_json(RUTA_CONFIGURACION_EJEMPLO)
    ruta_estado = RUTA_CONFIGURACION_EJEMPLO.with_name(
        "empresa_estado.json"
    )
    assert cargar_estado(ruta_estado, sistema)

    for producto in sistema.elementos_produccion.values():
        assert sistema.inventario.obtener_stock(producto) == {
            "actual": 0,
            "reservado": 0,
        }
