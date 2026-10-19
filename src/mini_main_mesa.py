import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.SysMRP_simple import SistemaMRP
from src.elementos import Insumo, Producto
from src.manufactura import (
    Colaborador,
    PeriodoOperacion,
    ProcesoManufactura,
    TareaDefinida,
    UnidadTrabajo,
)


def main():
    """Ejecuta paso a paso un ejemplo de fabricación de mesas."""
    # El sistema MRP administra los productos, el inventario, la BOM
    # (lista de materiales) y las órdenes de fabricación.
    sistema = SistemaMRP()

    # ---------------------------------------------------------------------
    # 1. Definición de los materiales y productos
    # ---------------------------------------------------------------------
    # La madera y los clavos son insumos: no se fabrican, se consumen.
    madera = Insumo("Madera", "m2", 50)
    clavos = Insumo("Clavos", "un", 2)

    # Una tabla necesita 2 m2 de madera y 10 clavos.
    tabla = Producto("Tabla", "un", 1)
    tabla.construir_bom_manual(madera, 2)
    tabla.construir_bom_manual(clavos, 10)

    # Una pata necesita 1 m2 de madera y 5 clavos.
    pata = Producto("Pata", "un", 1)
    pata.construir_bom_manual(madera, 1)
    pata.construir_bom_manual(clavos, 5)

    # La mesa terminada está compuesta por una tabla y cuatro patas.
    # Al agregar estos componentes se construye su lista de materiales.
    mesa = Producto("Mesa", "un", 1)
    mesa.construir_bom_manual(tabla, 1)
    mesa.construir_bom_manual(pata, 4)

    # ---------------------------------------------------------------------
    # 2. Carga del inventario inicial
    # ---------------------------------------------------------------------
    # Ya existe una tabla en stock. Las patas y las mesas todavía no fueron
    # fabricadas, por eso comienzan con cantidad cero.
    sistema.agregar_elemento(madera, stock_actual=100)
    sistema.agregar_elemento(clavos, stock_actual=500)
    sistema.agregar_elemento(tabla, stock_actual=1)
    sistema.agregar_elemento(pata)
    sistema.agregar_elemento(mesa)

    # ---------------------------------------------------------------------
    # 3. Definición del proceso de manufactura
    # ---------------------------------------------------------------------
    # Una unidad de trabajo representa una máquina o puesto de producción.
    # Los números indican capacidad, costo fijo y cantidad de operarios
    # permitidos, respectivamente.
    sierra = UnidadTrabajo("Sierra", 10, 120, 1)
    banco = UnidadTrabajo("Banco armado", 5, 80, 2)

    # Cada colaborador tiene un costo por hora y una lista de habilidades.
    carpintero = Colaborador("Ana", 25, ["corte", "armado"])
    armador = Colaborador("Luis", 22, ["armado"])

    # Las tareas describen qué se hace, cuánto demora, qué máquina utiliza,
    # quién la realiza y qué habilidad necesita.
    corte = TareaDefinida("Corte de componentes", 2, sierra, [carpintero], ["corte"])
    montaje = TareaDefinida("Armado y fijación", 1.5, banco, [armador], ["armado"])

    # El montaje depende del corte: primero se cortan las piezas y después
    # se ensamblan.
    montaje.agregar_subtarea(corte)

    # El proceso ordena las tareas que forman la fabricación de una mesa.
    proceso = ProcesoManufactura(mesa)
    proceso.modificar_proceso([corte, montaje])

    # Se asigna un período de trabajo a cada tarea. El segundo período
    # empieza cuando termina el primero para respetar la secuencia.
    periodos = [
        PeriodoOperacion(datetime(2026, 10, 20, 8), datetime(2026, 10, 20, 10)),
        PeriodoOperacion(datetime(2026, 10, 20, 10), datetime(2026, 10, 20, 11, 30)),
    ]

    # Se muestra la estructura completa de la mesa y el costo calculado
    # sumando el costo de todos sus componentes.
   
    print("BOM mesa")
    print(sistema.bom.arbol_texto(mesa))
    print(f"\nCosto de materiales por mesa: ${mesa.costo_unitario()}")

    # "Actual" es la cantidad física, "reservado" la cantidad asignada a
    # órdenes y "libre" lo que todavía puede utilizarse.
    print("\nStock inicial ")
    for nombre, elemento in sistema.elementos_produccion.items():
        stock = sistema.inventario.obtener_stock(elemento)
        print(
            f"{nombre}: actual={stock['actual']} "
            f"reservado={stock['reservado']} "
            f"libre={sistema.inventario.stock_libre(elemento)} "
            f"{elemento.unidad_medida}"
        )

    # ---------------------------------------------------------------------
    # 3. Persistencia y creación de la orden
    # ---------------------------------------------------------------------
    # Se guarda y se vuelve a cargar el sistema para simular que la
    # planificación puede continuarse en otra ejecución del programa.
    sistema.guardar_pickle("sistema_mrp.pkl")
    sistema = SistemaMRP.cargar_pickle("sistema_mrp.pkl")
    mesa = sistema.elementos_produccion["Mesa"]

    # La orden comienza en estado "creada".
    sistema.crear_orden_fabricacion("SOL-1", mesa, 2)
    solicitud = sistema.obtener_solicitud_por_id("SOL-1")
    print(f"\nid: {solicitud.id}, {solicitud.cantidad} {solicitud.producto.nombre}, Estado: {solicitud.estado}")

    # ---------------------------------------------------------------------
    # 4. Planificación de la orden
    # ---------------------------------------------------------------------
    # Al procesar la orden, el MRP verifica y reserva los materiales.
    # La orden pasa a estado "planificada".
    sistema.procesar_siguiente_solicitud()
    print(f"\nid: {solicitud.id} Estado: {solicitud.estado} (Reserva materiales)\n")


    #Impresion Materiales
    for nombre, elemento in sistema.elementos_produccion.items():
            stock = sistema.inventario.obtener_stock(elemento)
            print(
                f"{nombre}: actual={stock['actual']} "
                f"reservado={stock['reservado']} "
                f"libre={sistema.inventario.stock_libre(elemento)} "
                f"{elemento.unidad_medida}"
            )

    # La orden pasa a "en curso" y se inicia el proceso de manufactura.
    sistema.iniciar_produccion("SOL-1")
    tareas = proceso.iniciar_proceso(solicitud.cantidad, periodos)
    print(f"Estado: {solicitud.estado}")
    print("\nManufactura")

    print(
        f"Producto: {solicitud.producto.nombre} | "
        f"Cantidad: {solicitud.cantidad}"
    )
    print(f"Costo: ${proceso.calcular_costo_operativo()}")
    for tarea, periodo in zip(tareas, periodos):
        unidades = []
        for unidad in tarea.unidades_trabajo:
            unidades.append(unidad.nombre)

        colaboradores = []
        for colaborador in tarea.colaboradores:
            colaboradores.append(colaborador.nombre)

        print(
            f"Tarea: {tarea.nombre} -- "
            f"UT: {unidades} -- "
            f"Colaborador: {colaboradores} -- "
            f"Período: {periodo.inicio}-{periodo.fin}"
        )

    # Al finalizar se consumen los materiales reservados y se agregan
    # las dos mesas terminadas al inventario.
    sistema.finalizar_produccion("SOL-1")
    print(f"\n id: {solicitud.id}  Estado: {solicitud.estado}")
    print("\nStock final")
    for nombre, elemento in sistema.elementos_produccion.items():
        print(
            f"{nombre}: {sistema.inventario.stock_libre(elemento)} "
            f"{elemento.unidad_medida}"
        )

    # El costo total combina los materiales de todo el lote y el costo
    # operativo de las tareas de manufactura.
    costo_materiales = mesa.costo_unitario() * solicitud.cantidad
    costo_operativo = proceso.calcular_costo_operativo()

    print(f"\nCosto total: ${costo_materiales + costo_operativo}")

    # Se conserva el estado final de la orden y del inventario.
    sistema.guardar_pickle("sistema_mrp.pkl")


if __name__ == "__main__":
    main()
