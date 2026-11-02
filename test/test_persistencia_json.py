from pathlib import Path

from src.cargador_json import cargar_sistema_desde_json
from src.elementos import Insumo
from src.persistencia_json import cargar_estado, guardar_estado


RUTA_CONFIGURACION = (
    Path(__file__).resolve().parents[1]
    / "datos"
    / "empresa.json"
)


def _nuevo_sistema():
    return cargar_sistema_desde_json(RUTA_CONFIGURACION)


def test_persiste_inventario_y_solicitud_creada(tmp_path):
    sistema = _nuevo_sistema()
    madera = sistema.elementos_produccion["Madera"]
    sistema.inventario.agregar_stock(madera, 42)
    assert sistema.crear_orden_fabricacion(
        "SOL-1",
        sistema.elementos_produccion["Mesa"],
        2,
        solicitante="Cliente",
    )
    ruta_estado = tmp_path / "estado.json"

    guardar_estado(ruta_estado, sistema)
    restaurado = _nuevo_sistema()

    assert cargar_estado(ruta_estado, restaurado)
    assert restaurado.inventario.obtener_stock(
        restaurado.elementos_produccion["Madera"]
    ) == {"actual": 42, "reservado": 0}
    solicitud = restaurado.obtener_solicitud_por_id("SOL-1")
    assert solicitud.estado == "creada"
    assert solicitud.solicitante == "Cliente"
    assert restaurado.cola_solicitudes.ver_primero() == "SOL-1"


def test_reanuda_solicitud_en_curso_con_plan_y_avance(tmp_path):
    sistema = _nuevo_sistema()
    for elemento in sistema.elementos_produccion.values():
        if isinstance(elemento, Insumo):
            sistema.inventario.agregar_stock(elemento, 100)

    assert sistema.crear_orden_fabricacion(
        "SOL-1", sistema.elementos_produccion["Mesa"], 1
    )
    assert sistema.procesar_siguiente_solicitud()
    assert sistema.iniciar_produccion("SOL-1")
    sistema.fabricar_siguiente_producto("SOL-1")

    ruta_estado = tmp_path / "estado.json"
    guardar_estado(ruta_estado, sistema)
    restaurado = _nuevo_sistema()

    assert cargar_estado(ruta_estado, restaurado)
    solicitud = restaurado.obtener_solicitud_por_id("SOL-1")
    assert solicitud.estado == "en curso"
    plan = restaurado.obtener_plan_produccion("SOL-1")
    realizados = restaurado._fabricaciones_realizadas["SOL-1"]
    assert len(realizados) == 1

    while restaurado.fabricar_siguiente_producto("SOL-1") is not None:
        pass
    assert restaurado.finalizar_produccion("SOL-1")
    assert solicitud.estado == "finalizada"
    assert len(plan["orden_fabricacion"]) >= 1
