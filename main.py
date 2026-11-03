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
            f"x {solicitud.cantidad} | {solicitud.estado} | {solicitud.solicitante}"

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


def mostrar_cuellos_de_botella(sistema):
    """Imprime las unidades de trabajo con más horas acumuladas en la sesión."""
    cuellos = sistema.detectar_cuello()

    print("\nCuellos de botella")
    if not cuellos:
        print("No hay unidades de trabajo ocupadas.")
        return

    for posicion, carga in enumerate(cuellos, start=1):
        unidad = carga["unidad"]
        print(
            f"{posicion}. {unidad.nombre}: "
            f"{carga['horas_ocupadas']} horas acumuladas"
        )


def mostrar_historial_tareas(sistema):
    # Muestra el historial de tareas ejecutadas durante la sesión actual.
    historial = sistema.obtener_historial_tareas()

    print("\nHistorial de tareas")
    if not historial:
        print("No hay tareas ejecutadas en esta sesión.")
        return

    for ejecucion in historial:
        print(
            f"- {ejecucion['solicitud']} | "
            f"{ejecucion['producto'].nombre} | "
            f"{ejecucion['tarea'].nombre} | "
            f"{ejecucion['estado']}"
        )


def mostrar_tareas_cargadas(sistema):
    """Imprime todas las tareas definidas en los procesos cargados."""
    print("\nTareas cargadas")
    tareas_cargadas = [
        (producto, tarea)
        for producto in sistema.elementos_produccion.values()
        if isinstance(producto, Producto) and producto.proceso_manufactura
        for tarea in producto.proceso_manufactura.tareas
    ]

    if not tareas_cargadas:
        print("No hay tareas cargadas.")
        return

    for producto, tarea in tareas_cargadas:
        unidad = (
            tarea.unidad_trabajo.nombre
            if tarea.unidad_trabajo is not None
            else "Sin unidad de trabajo"
        )
        colaboradores = ", ".join(
            colaborador.nombre
            for colaborador in tarea.colaboradores_requeridos
        ) or "Sin colaboradores"
        habilidades = ", ".join(tarea.habilidades_requeridas) or "Sin habilidades"
        subtareas = ", ".join(subtarea.nombre for subtarea in tarea.subtareas)
        print(
            f"- {tarea.nombre} | Producto: {producto.nombre} | "
            f"Tiempo: {tarea.tiempo} h | UT: {unidad} | "
            f"Colaboradores: {colaboradores} | "
            f"Habilidades: {habilidades} | "
            f"Subtareas: {subtareas or 'Ninguna'}"
        )


def mostrar_unidades_trabajo(sistema):
    """Imprime todas las unidades de trabajo cargadas."""
    print("\nUnidades de trabajo")
    if not sistema.unidades_trabajo:
        print("No hay unidades de trabajo cargadas.")
        return

    for unidad in sistema.unidades_trabajo:
        print(
            f"- {unidad.nombre} | Capacidad máxima: "
            f"{unidad.capacidad_max_produccion} | "
            f"Costo fijo: ${unidad.costo_fijo:.2f} | "
            f"Capacidad de colaboradores: {unidad.capacidad_colaboradores} | "
            f"Períodos ocupados: {len(unidad.periodos_ocupados)}"
        )


def mostrar_colaboradores(sistema):
    """Imprime todos los colaboradores cargados."""
    print("\nColaboradores")
    if not sistema.colaboradores:
        print("No hay colaboradores cargados.")
        return

    for colaborador in sistema.colaboradores:
        habilidades = ", ".join(colaborador.habilidades) or "Sin habilidades"
        print(
            f"- {colaborador.nombre} | Costo por hora: "
            f"${colaborador.costo_por_hora:.2f} | "
            f"Habilidades: {habilidades} | "
            f"Períodos ocupados: {len(colaborador.periodos_ocupados)}"
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
    """Agrega al stock la cantidad elegida de un insumo."""
    insumos = [
        elemento
        for elemento in sistema.elementos_produccion.values()
        if isinstance(elemento, Insumo)
    ]
    if not insumos:
        print("No hay insumos para actualizar.")
        return

    print("\nInsumos disponibles")
    insumo = _seleccionar_elemento(insumos, "Número del insumo: ")
    if insumo is None:
        return

    cantidad = _leer_entero_positivo("Cantidad a comprar: ")
    if cantidad is None:
        return

    sistema.inventario.agregar_stock(insumo, cantidad)
    print(f"Se agregaron {cantidad} unidades a {insumo.nombre}.")


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


def _mostrar_insumos_faltantes(sistema, solicitud):
    """Muestra cuánto falta comprar de cada insumo requerido."""
    plan = sistema.bom.calcular_plan(
        solicitud.producto,
        solicitud.cantidad,
        sistema.inventario,
    )
    faltantes = []
    for insumo, cantidad_requerida in plan["insumos"].items():
        cantidad_disponible = sistema.inventario.stock_libre(insumo)
        cantidad_faltante = max(cantidad_requerida - cantidad_disponible, 0)
        if cantidad_faltante:
            faltantes.append((insumo, cantidad_faltante))

    if not faltantes:
        return False

    print("Insumos faltantes:")
    for insumo, cantidad in faltantes:
        print(f"- {insumo.nombre}: {cantidad} {insumo.unidad_medida}")
    return True


def _procesar_solicitud(sistema, solicitud):
    """Planifica, fabrica y finaliza una solicitud."""
    if solicitud.estado == "creada" and not sistema.procesar_siguiente_solicitud():
        _mostrar_insumos_faltantes(sistema, solicitud)
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
        if resultado is None:
            break
        sleep(5)  # aca valoramos mucho el realismo
        producto, cantidad_fabricada = resultado
        print(f"Fabricado: {producto.nombre} | Cantidad: {cantidad_fabricada}")

    if not sistema.finalizar_produccion(solicitud.id):
        raise EstadoSolicitudError(
            f"No se pudo finalizar la solicitud '{solicitud.id}'"
        )

    if (
        isinstance(solicitud.solicitante, str)
        and solicitud.solicitante.strip().casefold()
        == sistema.SOLICITANTE_INVENTARIO
    ):
        print(f"Estado: {solicitud.estado} (stock agregado al inventario)")
    else:
        print(f"Estado: {solicitud.estado} (pedido entregado a {solicitud.solicitante})")
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
        "4. Comprar insumo\n"
        "5. Crear solicitud\n"
        "6. Detectar cuellos de botella\n"
        "7. Mostrar historial de tareas\n"
        "8. Mostrar tareas cargadas\n"
        "9. Mostrar unidades de trabajo\n"
        "10. Mostrar colaboradores\n"
        "11. Salir"
    )


def ejecutar_menu(sistema, ruta_estado):
    """Lee opciones del usuario y ejecuta la acción correspondiente."""
    while True:
        mostrar_menu()
        opcion = input("Elegí una opción: ").strip()

        if opcion == "11":
            guardar_estado(ruta_estado, sistema)
            print("Saliendo del sistema.")
            return
        if opcion not in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10"):
            print("Opción inválida. Elegí un número del 1 al 11.")
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
            elif opcion == "5":
                crear_solicitud(sistema)
            elif opcion == "6":
                mostrar_cuellos_de_botella(sistema)
            elif opcion == "7":
                mostrar_historial_tareas(sistema)
            elif opcion == "8":
                mostrar_tareas_cargadas(sistema)
            elif opcion == "9":
                mostrar_unidades_trabajo(sistema)
            else:
                mostrar_colaboradores(sistema)
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
