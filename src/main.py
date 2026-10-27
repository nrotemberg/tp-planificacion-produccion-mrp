import argparse
from pathlib import Path

from src.cargador_json import cargar_sistema_desde_json, ErrorConfiguracion
from src.excepciones import MRPError, EstadoSolicitudError, ErrorConfiguracion
from src.elementos import ComponenteBOM, ElementoProduccion, Insumo, Producto
from src.SysMRP_simple import SistemaMRP
from src.manufactura import (
    Colaborador,
    PeriodoOperacion,
    ProcesoManufactura,
    TareaDefinida,
    TareaEnCurso,
    UnidadTrabajo,
)
from src.solicitudes import Solicitud

__all__ = [
    "ElementoProduccion",
    "Insumo",
    "ComponenteBOM",
    "Producto",
    "ProcesoManufactura",
    "TareaDefinida",
    "TareaEnCurso",
    "UnidadTrabajo",
    "Colaborador",
    "PeriodoOperacion",
    "Solicitud",
    "SistemaMRP",
    "hola_mundo",
]

def mostrar_inventario(sistema):
    print("\nStock final")

    for nombre, elemento in sistema.elementos_produccion.items():
        stock = sistema.inventario.obtener_stock(elemento)

        print(
            f"{nombre}: "
            f"actual={stock['actual']} "
            f"reservado={stock['reservado']} "
            f"libre={sistema.inventario.stock_libre(elemento)} "
            f"{elemento.unidad_medida}"
        )


def ejecutar_simulacion(sistema):
    """Coordina las órdenes en el orden en que fueron cargadas."""
    for solicitud in tuple(sistema.solicitudes.values()):
        print(
            f"\nSolicitud: {solicitud.id} | "
            f"Producto: {solicitud.producto.nombre} | "
            f"Cantidad: {solicitud.cantidad}"
        )

        if not sistema.procesar_siguiente_solicitud():
            raise EstadoSolicitudError(
                f"No se pudo planificar '{solicitud.id}'. "
                "Revisá los materiales disponibles."
            )

        proceso = solicitud.producto.proceso_manufactura
        periodos = sistema.obtener_periodos_solicitud(solicitud.id)

        tareas = proceso.iniciar_proceso(
            solicitud.cantidad,
            list(periodos),
        )

        if not sistema.iniciar_produccion(solicitud.id):
            for tarea in tareas:
                tarea.cancelar()

            raise EstadoSolicitudError(
                f"No se pudo iniciar '{solicitud.id}'"
            )

        print(f"Estado: {solicitud.estado}")

        for tarea in tareas:
            tarea.actualizar_estado("en_curso")
            print(f"Tarea: {tarea.nombre}")

            # Simulación: no espera el transcurso del tiempo real.
            tarea.finalizar()

        if not sistema.finalizar_produccion(solicitud.id):
            raise EstadoSolicitudError(
                f"No se pudo finalizar '{solicitud.id}'"
            )

        print(f"Estado: {solicitud.estado}")

        costo_total = (
            solicitud.producto.costo_unitario()
            * solicitud.cantidad
        )

        print(f"Costo estándar del lote: ${costo_total:.2f}")


def main():
    parser = argparse.ArgumentParser(
        description="Simula la producción con datos de un archivo JSON."
    )

    archivo_por_defecto = (
        Path(__file__).resolve().parents[1]
        / "datos"
        / "empresa.json"
    )

    parser.add_argument(
        "archivo",
        nargs="?",
        type=Path,
        default=archivo_por_defecto,
        help="Archivo JSON de configuración",
    )

    argumentos = parser.parse_args()

    try:
        sistema = cargar_sistema_desde_json(argumentos.archivo)

        print("Configuración cargada correctamente.")
        print("Simulación de producción, sin espera en tiempo real.")

        ejecutar_simulacion(sistema)
        mostrar_inventario(sistema)

    except (ErrorConfiguracion, MRPError) as error:
        print(f"\nNo se pudo completar la simulación: {error}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())