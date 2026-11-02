import argparse
from pathlib import Path
from time import sleep

from src.cargador_json import cargar_sistema_desde_json
from src.elementos import Insumo, Producto
from src.excepciones import ErrorConfiguracion, EstadoSolicitudError, MRPError
from src.persistencia_json import cargar_estado, guardar_estado


def mostrar_solicitudes(sistema):
    """Imprime las solicitudes registradas y sus estados actuales."""
    print("\nSolicitudes")
    if not sistema.solicitudes:
        print("No hay solicitudes.")
        return

    for solicitud in sistema.solicitudes.values():
        print(
            f"- {solicitud.id}: {solicitud.producto.nombre} "
            f"x {solicitud.cantidad} | {solicitud.estado}"
        )


def mostrar_inventario(sistema):
    """Imprime el stock actual, reservado y libre de cada elemento."""
    print("\nInventario")
    for nombre, elemento in sistema.elementos_produccion.items():
        stock = sistema.inventario.obtener_stock(elemento)
        print(
            f"- {nombre}: actual={stock['actual']} "
            f"reservado={stock['reservado']} "
            f"libre={sistema.inventario.stock_libre(elemento)} "
            f"{elemento.unidad_medida}"
        )


def _leer_entero_positivo(mensaje):
    try:
        cantidad = int(input(mensaje).strip())
    except ValueError:
        print("La cantidad debe ser un entero positivo.")
        return None

    if cantidad <= 0:
        print("La cantidad debe ser un entero positivo.")
        return None
    return cantidad


def _seleccionar_elemento(elementos, mensaje):
    elementos = list(elementos)
    if not elementos:
        print("No hay elementos disponibles.")
        return None

    for indice, elemento in enumerate(elementos, start=1):
        print(f"{indice}. {elemento.nombre}")

    try:
        seleccion = int(input(mensaje).strip())
    except ValueError:
        print("La opción debe ser un número.")
        return None

    if not 1 <= seleccion <= len(elementos):
        print(f"Elegí un número del 1 al {len(elementos)}.")
        return None
    return elementos[seleccion - 1]


def agregar_stock(sistema):
    """Agrega 100 unidades al stock de cada insumo."""
    insumos = [
        elemento
        for elemento in sistema.elementos_produccion.values()
        if isinstance(elemento, Insumo)
    ]
    if not insumos:
        print("No hay insumos para actualizar.")
        return

    for insumo in insumos:
        sistema.inventario.agregar_stock(insumo, 100)
        print(f"Se agregaron 100 unidades a {insumo.nombre}.")


def _productos_fabricables(sistema):
    """Devuelve todos los productos con un proceso de manufactura."""
    return [
        elemento
        for elemento in sistema.elementos_produccion.values()
        if isinstance(elemento, Producto)
        and elemento.proceso_manufactura
        and elemento.proceso_manufactura.tareas
    ]


def crear_solicitud(sistema):
    """Crea una solicitud para un producto con tareas de manufactura."""
    productos = _productos_fabricables(sistema)

    print("\nProductos fabricables")
    if not productos:
        print("No hay productos fabricables configurados.")
        return
    producto = _seleccionar_elemento(productos, "Número del producto: ")
    if producto is None:
        return

    cantidad = _leer_entero_positivo("Cantidad: ")
    if cantidad is None:
        return

    solicitante = input("Solicitante: ").strip() or "Sin especificar"
    numero = 1
    while f"SOL-{numero}" in sistema.solicitudes:
        numero += 1

    identificador = f"SOL-{numero}"
    if sistema.crear_orden_fabricacion(
        identificador,
        producto,
        cantidad,
        solicitante=solicitante,
    ):
        print(f"Solicitud {identificador} creada.")


def _procesar_solicitud(sistema, solicitud):
    """Planifica, fabrica y finaliza una solicitud."""
    if solicitud.estado == "creada" and not sistema.procesar_siguiente_solicitud():
        raise EstadoSolicitudError(
            f"No se pudo planificar '{solicitud.id}': "
            "faltan materiales o recursos disponibles"
        )

    cantidad = sistema.obtener_cantidad_a_fabricar(solicitud.id)
    fin_estimado = sistema.obtener_fin_estimado(solicitud.id)
    print(
        f"Desde stock: {solicitud.cantidad - cantidad} | "
        f"A fabricar: {cantidad}"
    )
    print(
        "Finalización estimada: "
        f"{fin_estimado.astimezone().strftime('%Y-%m-%d %H:%M')}"
    )

    if solicitud.estado == "planificada" and not sistema.iniciar_produccion(
        solicitud.id
    ):
        raise EstadoSolicitudError(
            f"No se pudo iniciar la solicitud '{solicitud.id}'"
        )
    if solicitud.estado not in ("planificada", "en curso"):
        raise EstadoSolicitudError(
            f"La solicitud '{solicitud.id}' no puede continuar desde "
            f"el estado '{solicitud.estado}'"
        )

    while True:
        resultado = sistema.fabricar_siguiente_producto(solicitud.id)
        sleep(5)  #aca valoramos mucho el realismo
        if resultado is None:
            break
        producto, cantidad_fabricada = resultado
        print(f"Fabricado: {producto.nombre} | Cantidad: {cantidad_fabricada}")

    if not sistema.finalizar_produccion(solicitud.id):
        raise EstadoSolicitudError(
            f"No se pudo finalizar la solicitud '{solicitud.id}'"
        )

    print(f"Estado: {solicitud.estado} (pedido entregado)")
    costo_unitario = solicitud.producto.costo_unitario()
    costo_fabricacion = sistema.calcular_costo_fabricacion(solicitud.id)
    print(f"Costo estándar de fabricación nueva: ${costo_fabricacion:.2f}")
    print(f"Valor estándar del pedido: ${costo_unitario * solicitud.cantidad:.2f}")


def ejecutar_flujo(sistema):
    """Procesa completa sólo la siguiente solicitud de la cola FIFO."""
    if not sistema.cola_solicitudes:
        print("\nNo hay solicitudes pendientes.")
        return

    solicitud = sistema.obtener_solicitud_por_id(
        sistema.cola_solicitudes.ver_primero()
    )
    print(
        f"\nProcesando {solicitud.id}: "
        f"{solicitud.producto.nombre} x {solicitud.cantidad}"
    )
    try:
        _procesar_solicitud(sistema, solicitud)
    except MRPError as error:
        print(f"No se pudo completar {solicitud.id}: {error}")


def mostrar_menu():
    """Muestra las opciones disponibles en la interfaz de terminal."""
    print(
        "\n=== Sistema MRP ===\n"
        "1. Procesar siguiente solicitud (FIFO)\n"
        "2. Mostrar solicitudes\n"
        "3. Mostrar inventario\n"
        "4. Agregar 100 unidades a cada insumo\n"
        "5. Crear solicitud\n"
        "6. Salir"
    )


def ejecutar_menu(sistema, ruta_estado):
    """Lee opciones del usuario y ejecuta la acción correspondiente."""
    while True:
        mostrar_menu()
        opcion = input("Elegí una opción: ").strip()

        if opcion == "6":
            guardar_estado(ruta_estado, sistema)
            print("Saliendo del sistema.")
            return
        if opcion not in ("1", "2", "3", "4", "5"):
            print("Opción inválida. Elegí un número del 1 al 6.")
            continue

        try:
            if opcion == "1":
                ejecutar_flujo(sistema)
            elif opcion == "2":
                mostrar_solicitudes(sistema)
            elif opcion == "3":
                mostrar_inventario(sistema)
            elif opcion == "4":
                agregar_stock(sistema)
            else:
                crear_solicitud(sistema)
        except MRPError as error:
            print(f"\nNo se pudo completar la operación: {error}")
        guardar_estado(ruta_estado, sistema)


def main():
    """Carga la configuración e inicia el menú interactivo."""
    parser = argparse.ArgumentParser(
        description="Gestiona el flujo de producción desde la terminal."
    )
    archivo_por_defecto = (
        Path(__file__).resolve().parent / "datos" / "empresa.json"
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
        ruta_estado = argumentos.archivo.with_name(
            f"{argumentos.archivo.stem}_estado.json"
        )
        if not cargar_estado(ruta_estado, sistema):
            guardar_estado(ruta_estado, sistema)
    except ErrorConfiguracion as error:
        print(f"\nNo se pudo cargar la configuración o el estado: {error}")
        return 1

    print(f"Configuración cargada: {argumentos.archivo}")
    try:
        ejecutar_menu(sistema, ruta_estado)
    except (EOFError, KeyboardInterrupt):
        print("\nSaliendo del sistema.")
        try:
            guardar_estado(ruta_estado, sistema)
        except ErrorConfiguracion as error:
            print(f"No se pudo guardar el estado: {error}")
            return 1
    except ErrorConfiguracion as error:
        print(f"\nNo se pudo guardar el estado: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
