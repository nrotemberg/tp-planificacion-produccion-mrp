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
    for solicitud in tuple(sistema.solicitudes.values()):
        if not sistema.procesar_siguiente_solicitud():
            raise EstadoSolicitudError(
                f"No se pudo planificar '{solicitud.id}': "
                "faltan materiales"
            )

        cantidad = sistema.obtener_cantidad_a_fabricar(
            solicitud.id
        )

        print(
            f"\nSolicitud: {solicitud.id} | "
            f"Pedidas: {solicitud.cantidad}"
        )
        print(
            f"Desde stock: {solicitud.cantidad - cantidad} | "
            f"A fabricar: {cantidad}"
        )

        if not sistema.iniciar_produccion(solicitud.id):
            raise EstadoSolicitudError(
                "No se pudo iniciar la solicitud"
            )

        while True:
            resultado = sistema.fabricar_siguiente_producto(
                solicitud.id
            )

            if resultado is None:
                break

            producto, cantidad_fabricada = resultado

            print(
                f"Fabricado: {producto.nombre} | "
                f"Cantidad: {cantidad_fabricada}"
            )

        if not sistema.finalizar_produccion(solicitud.id):
            raise EstadoSolicitudError(
                "No se pudo finalizar la solicitud"
            )

        print(
            f"Estado: {solicitud.estado} "
            "(pedido entregado)"
        )

        costo_unitario = solicitud.producto.costo_unitario()
        costo_fabricacion = sistema.calcular_costo_fabricacion(
            solicitud.id
        )

        print(
            "Costo estándar de fabricación nueva: "
            f"${costo_fabricacion:.2f}"
        )
        print(
            "Valor estándar del pedido: "
            f"${costo_unitario * solicitud.cantidad:.2f}"
        )


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