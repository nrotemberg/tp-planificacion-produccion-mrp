import sys
from pathlib import Path
from datetime import datetime
from src.manufactura import (
    Colaborador,
    PeriodoOperacion,
    ProcesoManufactura,
    TareaDefinida,
    UnidadTrabajo,
)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.elementos import ComponenteBOM, Insumo, Producto
from src.solicitudes import Solicitud
from src.SysMRP_simple import SistemaMRP
from src.bom import GestorBOM

def crear_ranger_ejemplo():
    """Construye una BOM pequena pero representativa de una Ranger."""
    aluminio = Insumo("Aluminio", "kg", 5)
    acero = Insumo("Acero", "kg", 8)
    goma = Insumo("Goma", "unidad", 12)
    tela = Insumo("Tela", "m2", 10)
    vidrio = Insumo("Vidrio", "unidad", 15)

    bloque_motor = Producto("Bloque motor", "unidad", 1)
    bloque_motor.agregar_a_BOM(ComponenteBOM(aluminio, 18))
    bloque_motor.agregar_a_BOM(ComponenteBOM(acero, 6))

    motor_v6 = Producto("Motor V6", "unidad", 1)
    motor_v6.agregar_a_BOM(ComponenteBOM(bloque_motor, 1))
    motor_v6.agregar_a_BOM(ComponenteBOM(acero, 4))

    chasis = Producto("Chasis", "unidad", 1)
    chasis.agregar_a_BOM(ComponenteBOM(acero, 35))
    chasis.agregar_a_BOM(ComponenteBOM(aluminio, 8))

    interior = Producto("Interior", "unidad", 1)
    interior.agregar_a_BOM(ComponenteBOM(tela, 12))
    interior.agregar_a_BOM(ComponenteBOM(vidrio, 6))

    ranger = Producto("Ranger", "unidad", 1)
    ranger.agregar_a_BOM(ComponenteBOM(motor_v6, 1))
    ranger.agregar_a_BOM(ComponenteBOM(chasis, 1))
    ranger.agregar_a_BOM(ComponenteBOM(goma, 4))
    ranger.agregar_a_BOM(ComponenteBOM(interior, 1))
    return ranger


def mostrar_ejemplo_ranger():
    """Imprime la BOM completa de 10 Rangers para verla manualmente."""
    print(GestorBOM().arbol_texto(crear_ranger_ejemplo(), 10))

if __name__ == "__main__":
    mostrar_ejemplo_ranger()

def crear_sistema():
    madera = Insumo("Madera", "unidad", 5)
    mesa = Producto("Mesa", "unidad", 1)
    mesa.agregar_a_BOM(ComponenteBOM(madera, 2))

    proceso = ProcesoManufactura(mesa)
    proceso.agregar_tarea(
        TareaDefinida(
            nombre="Fabricar mesa",
            tiempo=1,
            unidad_trabajo=None,
            colaboradores_requeridos=[],
            habilidades_requeridas=[],
        )
    )

    solicitud = Solicitud(1, "Deposito", mesa, 2)

    sistema = SistemaMRP()
    sistema.agregar_elemento(madera, 10)
    sistema.agregar_elemento(mesa)
    sistema.crear_solicitud(solicitud)

    return sistema, solicitud, madera, mesa

def test_agregar_elementos():
    sistema = SistemaMRP()
    madera = Insumo("Madera", "unidad", 5)
    assert sistema.agregar_elemento(madera, 10, 2) is True
    assert sistema.elementos_produccion == {"Madera": madera}
    assert sistema.inventario.stock[madera] == {"actual": 10, "reservado": 2}

def test_no_agregar_elemento_duplicado():
    sistema = SistemaMRP()
    madera = Insumo("Madera", "unidad", 5)
    assert sistema.agregar_elemento(madera) is True
    assert sistema.agregar_elemento(madera) is False
    assert sistema.elementos_produccion == {"Madera": madera}


def test_detectar_cuello_devuelve_hasta_tres_unidades_por_horas_ocupadas():
    sistema = SistemaMRP()
    unidades = [
        UnidadTrabajo("Unidad 1", 10, 1, 1),
        UnidadTrabajo("Unidad 2", 10, 1, 1),
        UnidadTrabajo("Unidad 3", 10, 1, 1),
        UnidadTrabajo("Unidad 4", 10, 1, 1),
    ]
    for unidad in unidades:
        sistema.agregar_unidad_trabajo(unidad)

    unidades[0].asignar_periodo(
        PeriodoOperacion(datetime(2026, 11, 1, 8), datetime(2026, 11, 1, 10))
    )
    unidades[1].asignar_periodo(
        PeriodoOperacion(datetime(2026, 11, 1, 8), datetime(2026, 11, 1, 13))
    )
    unidades[2].asignar_periodo(
        PeriodoOperacion(datetime(2026, 11, 1, 8), datetime(2026, 11, 1, 12))
    )
    unidades[3].asignar_periodo(
        PeriodoOperacion(datetime(2026, 11, 1, 8), datetime(2026, 11, 1, 9))
    )

    assert sistema.detectar_cuello() == [
        {"unidad": unidades[1], "horas_ocupadas": 5},
        {"unidad": unidades[2], "horas_ocupadas": 4},
        {"unidad": unidades[0], "horas_ocupadas": 2},
    ]


def test_detectar_cuello_omite_unidades_sin_periodos_y_devuelve_lista_vacia():
    sistema = SistemaMRP()
    unidad = UnidadTrabajo("Unidad", 10, 1, 1)
    sistema.agregar_unidad_trabajo(unidad)

    assert sistema.detectar_cuello() == []

def test_crear_y_obtener_solicitud_por_id():
    sistema, solicitud, _, _ = crear_sistema()
    assert sistema.obtener_solicitud_por_id(1) is solicitud
    assert sistema.obtener_solicitud_por_id(99) is None
    assert sistema.crear_solicitud(solicitud) is False

def test_crear_orden_fabricacion_crea_y_registra_solicitud():
    sistema = SistemaMRP()
    mesa = Producto("Mesa", "unidad", 1)
    sistema.agregar_elemento(mesa)
    resultado = sistema.crear_orden_fabricacion(1, mesa, 2, solicitante="Deposito")
    assert resultado is True

    solicitud = sistema.obtener_solicitud_por_id(1)
    assert solicitud is not None
    assert solicitud.id == 1
    assert solicitud.solicitante == "Deposito"
    assert solicitud.producto is mesa
    assert solicitud.cantidad == 2
    assert solicitud.estado == "creada"

def test_verificar_y_reservar_stock():
    sistema, solicitud, madera, _ = crear_sistema()
    assert sistema.verificar_stock(1) is True
    assert sistema.reservar_recursos(1) is True
    assert sistema.inventario.stock[madera]["reservado"] == 4
    assert solicitud.estado == "planificada"

def test_no_reservar_si_no_hay_stock():
    sistema, _, madera, _ = crear_sistema()
    sistema.inventario.stock[madera]["actual"] = 3
    assert sistema.verificar_stock(1) is False
    assert sistema.reservar_recursos(1) is False
    assert sistema.inventario.stock[madera]["reservado"] == 0

def test_no_reservar_dos_veces_la_misma_solicitud():
    sistema, solicitud, madera, _ = crear_sistema()
    assert sistema.reservar_recursos(1) is True
    stock_reservado = sistema.inventario.stock[madera]["reservado"]
    assert sistema.reservar_recursos(1) is False
    assert sistema.inventario.stock[madera]["reservado"] == stock_reservado
    assert solicitud.estado == "planificada"

def test_reservar_recursos_planifica_la_solicitud_en_el_sistema():
    sistema, _, _, _ = crear_sistema()
    assert sistema.reservar_recursos(1) is True


def test_programa_en_paralelo_tareas_con_recursos_distintos():
    madera = Insumo("Madera", "unidad", 1)
    mesa = Producto("Mesa", "unidad", 1)
    mesa.agregar_a_BOM(ComponenteBOM(madera, 1))
    proceso = ProcesoManufactura(mesa)

    for indice in (1, 2):
        colaborador = Colaborador(f"Colaborador {indice}", 1, [])
        unidad = UnidadTrabajo(f"Unidad {indice}", 10, 1, 1)
        tarea = TareaDefinida(
            f"Tarea {indice}",
            1,
            unidad,
            [colaborador],
            [],
        )
        proceso.agregar_tarea(tarea)

    sistema = SistemaMRP()
    sistema.agregar_elemento(madera, 10)
    sistema.agregar_elemento(mesa)
    solicitud = Solicitud(
        "SOL-PARALELO",
        "Deposito",
        mesa,
        2,
    )
    sistema.crear_solicitud(solicitud)

    assert sistema.reservar_recursos(solicitud.id) is True
    periodos = sistema.obtener_programacion_produccion(solicitud.id)[mesa]
    assert periodos[0].inicio == periodos[1].inicio
    assert periodos[0].fin == periodos[1].fin
    assert sistema.obtener_fin_estimado(solicitud.id) == periodos[0].fin


def test_serializa_tareas_que_comparten_colaborador():
    madera = Insumo("Madera", "unidad", 1)
    mesa = Producto("Mesa", "unidad", 1)
    mesa.agregar_a_BOM(ComponenteBOM(madera, 1))
    proceso = ProcesoManufactura(mesa)
    colaborador = Colaborador("Ana", 1, [])

    for indice in (1, 2):
        tarea = TareaDefinida(
            f"Tarea {indice}",
            1,
            UnidadTrabajo(f"Unidad {indice}", 10, 1, 1),
            [colaborador],
            [],
        )
        proceso.agregar_tarea(tarea)

    sistema = SistemaMRP()
    sistema.agregar_elemento(madera, 10)
    sistema.agregar_elemento(mesa)
    solicitud = Solicitud(
        "SOL-SERIAL",
        "Deposito",
        mesa,
        2,
    )
    sistema.crear_solicitud(solicitud)

    assert sistema.reservar_recursos(solicitud.id) is True
    primero, segundo = sistema.obtener_programacion_produccion(
        solicitud.id
    )[mesa]
    assert segundo.inicio == primero.fin


def test_iniciar_y_finalizar_produccion_consumen_stock():
    sistema, solicitud, madera, mesa = crear_sistema()

    assert sistema.reservar_recursos(1) is True
    assert sistema.iniciar_produccion(1) is True
    assert solicitud.estado == "en curso"

    assert sistema.fabricar_siguiente_producto(1) == (mesa, 2)

    # La fabricación consume madera y deja las mesas reservadas.
    assert sistema.inventario.obtener_stock(madera) == {
        "actual": 6,
        "reservado": 0,
    }
    assert sistema.inventario.obtener_stock(mesa) == {
        "actual": 2,
        "reservado": 2,
    }

    # No quedan productos pendientes de fabricación.
    assert sistema.fabricar_siguiente_producto(1) is None

    assert sistema.finalizar_produccion(1) is True
    assert solicitud.estado == "finalizada"

    # La entrega retira las dos mesas del inventario.
    assert sistema.inventario.obtener_stock(mesa) == {
        "actual": 0,
        "reservado": 0,
    }

def test_no_iniciar_dos_veces_la_misma_solicitud():
    sistema, solicitud, _, _ = crear_sistema()
    sistema.reservar_recursos(1)
    assert sistema.iniciar_produccion(1) is True
    assert solicitud.estado == "en curso"
    assert sistema.iniciar_produccion(1) is False
    assert solicitud.estado == "en curso"

def test_no_finalizar_dos_veces_la_misma_solicitud():
    sistema, solicitud, madera, mesa = crear_sistema()

    assert sistema.reservar_recursos(1) is True
    assert sistema.iniciar_produccion(1) is True
    assert sistema.fabricar_siguiente_producto(1) == (mesa, 2)
    assert sistema.finalizar_produccion(1) is True

    stock_madera = dict(
        sistema.inventario.obtener_stock(madera)
    )
    stock_mesa = dict(
        sistema.inventario.obtener_stock(mesa)
    )

    assert sistema.finalizar_produccion(1) is False

    assert sistema.inventario.obtener_stock(madera) == stock_madera
    assert sistema.inventario.obtener_stock(mesa) == stock_mesa
    assert solicitud.estado == "finalizada"

def test_bom_anidada_reserva_el_stock_de_los_insumos():
    madera = Insumo("Madera", "unidad", 5)
    base = Producto("Base", "unidad", 1)
    mesa = Producto("Mesa", "unidad", 1)

    base.agregar_a_BOM(ComponenteBOM(madera, 3))
    mesa.agregar_a_BOM(ComponenteBOM(base, 2))

    for producto in (base, mesa):
        proceso = ProcesoManufactura(producto)
        proceso.agregar_tarea(
            TareaDefinida(
                nombre=f"Fabricar {producto.nombre}",
                tiempo=1,
                unidad_trabajo=None,
                colaboradores_requeridos=[],
                habilidades_requeridas=[],
            )
        )

    solicitud = Solicitud(1, "Deposito", mesa, 2)

    sistema = SistemaMRP()
    sistema.agregar_elemento(madera, 20)
    sistema.agregar_elemento(base)
    sistema.agregar_elemento(mesa)
    sistema.crear_solicitud(solicitud)

    assert sistema.reservar_recursos(1) is True

    assert sistema.inventario.obtener_stock(madera) == {
        "actual": 20,
        "reservado": 12,
    }

    plan = sistema.obtener_plan_produccion(1)

    assert plan["a_fabricar"] == {
        base: 4,
        mesa: 2,
    }
    assert plan["orden_fabricacion"] == (base, mesa)

def test_arbol_texto_muestra_bom_completa_sin_consultar_stock(capsys):
    print(GestorBOM().arbol_texto(crear_ranger_ejemplo(), 10))
    salida = capsys.readouterr().out
    assert salida == (
        "Ranger x 10\n"
        "+-- Motor V6 x 10\n"
        "|   +-- Bloque motor x 10\n"
        "|   |   +-- Aluminio x 180\n"
        "|   |   `-- Acero x 60\n"
        "|   `-- Acero x 40\n"
        "+-- Chasis x 10\n"
        "|   +-- Acero x 350\n"
        "|   `-- Aluminio x 80\n"
        "+-- Goma x 40\n"
        "`-- Interior x 10\n"
        "    +-- Tela x 120\n"
        "    `-- Vidrio x 60\n")

def test_calcular_requerimientos_agrega_elementos_repetidos():
    ranger = crear_ranger_ejemplo()

    insumos, _ = GestorBOM().calcular_requerimientos(ranger, 10)
    cantidades_por_nombre = {insumo.nombre: cantidad
        for insumo, cantidad in insumos.items()}

    assert cantidades_por_nombre["Aluminio"] == 260
    assert cantidades_por_nombre["Acero"] == 450
    assert cantidades_por_nombre["Goma"] == 40
    assert cantidades_por_nombre["Tela"] == 120
    assert cantidades_por_nombre["Vidrio"] == 60

def test_bom_considera_stock_de_subproducto_intermedio():
    aluminio = Insumo("Aluminio", "unidad", 5)
    v6 = Producto("V6", "unidad", 1)
    ranger = Producto("Ranger", "unidad", 1)
    v6.agregar_a_BOM(ComponenteBOM(aluminio, 2))
    ranger.agregar_a_BOM(ComponenteBOM(v6, 1))
    solicitud = Solicitud(1, "Deposito", ranger, 10)
    sistema = SistemaMRP()
    sistema.agregar_elemento(aluminio, 20)
    sistema.agregar_elemento(v6, 4)
    sistema.agregar_elemento(ranger)
    sistema.crear_solicitud(solicitud)
    bom_original = list(ranger.lista_elementos_bom)
    bom_v6_original = list(v6.lista_elementos_bom)
    faltantes, _ = sistema._obtener_plan_materiales(solicitud)

    assert faltantes == {aluminio: 12}
    assert list(ranger.lista_elementos_bom) == bom_original
    assert list(v6.lista_elementos_bom) == bom_v6_original

def test_verificar_stock_considera_subproductos_y_requerimientos_netos():
    aluminio = Insumo("Aluminio", "unidad", 5)
    v6 = Producto("V6", "unidad", 1)
    ranger = Producto("Ranger", "unidad", 1)
    v6.agregar_a_BOM(ComponenteBOM(aluminio, 2))
    ranger.agregar_a_BOM(ComponenteBOM(v6, 1))
    solicitud = Solicitud(1, "Deposito", ranger, 10)
    sistema = SistemaMRP()
    sistema.agregar_elemento(aluminio, 12)
    sistema.agregar_elemento(v6, 4)
    sistema.agregar_elemento(ranger)
    sistema.crear_solicitud(solicitud)

    # Los 4 V6 disponibles cubren parte de la demanda.
    # Solo hacen falta materiales para fabricar los 6 V6 restantes.
    assert sistema.verificar_stock(1) is True
    sistema.inventario.stock[aluminio]["actual"] = 11
    assert sistema.verificar_stock(1) is False

def test_reservar_y_consumir_stock_intermedio():
    aluminio = Insumo("Aluminio", "unidad", 5)
    v6 = Producto("V6", "unidad", 1)
    ranger = Producto("Ranger", "unidad", 1)

    v6.agregar_a_BOM(ComponenteBOM(aluminio, 2))
    ranger.agregar_a_BOM(ComponenteBOM(v6, 1))

    for producto in (v6, ranger):
        proceso = ProcesoManufactura(producto)
        proceso.agregar_tarea(
            TareaDefinida(
                nombre=f"Fabricar {producto.nombre}",
                tiempo=0.5,
                unidad_trabajo=None,
                colaboradores_requeridos=[],
                habilidades_requeridas=[],
            )
        )

    solicitud = Solicitud(1, "Deposito", ranger, 10)

    sistema = SistemaMRP()
    sistema.agregar_elemento(aluminio, 20)
    sistema.agregar_elemento(v6, 4)
    sistema.agregar_elemento(ranger)
    sistema.crear_solicitud(solicitud)

    assert sistema.reservar_recursos(1) is True

    # Se aprovechan cuatro motores existentes y se fabrican seis.
    plan = sistema.obtener_plan_produccion(1)
    assert plan["a_fabricar"] == {v6: 6, ranger: 10}
    assert plan["orden_fabricacion"] == (v6, ranger)

    assert sistema.inventario.obtener_stock(v6) == {
        "actual": 4,
        "reservado": 4,
    }
    assert sistema.inventario.obtener_stock(aluminio) == {
        "actual": 20,
        "reservado": 12,
    }

    assert sistema.iniciar_produccion(1) is True

    # Los seis motores nuevos se suman a los cuatro existentes.
    assert sistema.fabricar_siguiente_producto(1) == (v6, 6)
    assert sistema.inventario.obtener_stock(v6) == {
        "actual": 10,
        "reservado": 10,
    }
    assert sistema.inventario.obtener_stock(aluminio) == {
        "actual": 8,
        "reservado": 0,
    }

    # Fabricar las diez camionetas consume los diez motores.
    assert sistema.fabricar_siguiente_producto(1) == (ranger, 10)
    assert sistema.inventario.obtener_stock(v6) == {
        "actual": 0,
        "reservado": 0,
    }
    assert sistema.inventario.obtener_stock(ranger) == {
        "actual": 10,
        "reservado": 10,
    }

    assert sistema.fabricar_siguiente_producto(1) is None
    assert sistema.finalizar_produccion(1) is True
    assert solicitud.estado == "finalizada"

    assert sistema.inventario.obtener_stock(ranger) == {
        "actual": 0,
        "reservado": 0,
    }

def test_no_se_puede_finalizar_solicitud_sin_iniciarla():
    sistema, _, _, _ = crear_sistema()
    assert sistema.finalizar_produccion(1) is False

def test_no_se_puede_iniciar_solicitud_sin_planificarla():
    sistema, solicitud, _, _ = crear_sistema()
    assert sistema.iniciar_produccion(1) is False
    assert solicitud.estado == "creada"

def test_metodos_rechazan_id_inexistente():
    sistema = SistemaMRP()
    assert sistema.verificar_stock(99) is False
    assert sistema.reservar_recursos(99) is False
    assert sistema.consumir_stock(99) is False
    assert sistema.iniciar_produccion(99) is False
    assert sistema.finalizar_produccion(99) is False

def test_procesar_solicitudes_respeta_el_orden_fifo():
    sistema = SistemaMRP()

    madera = Insumo("Madera", "unidad", 5)
    mesa = Producto("Mesa", "unidad", 1)
    mesa.agregar_a_BOM(ComponenteBOM(madera, 1))

    proceso = ProcesoManufactura(mesa)
    colaborador = Colaborador("Ana", 1, [])
    proceso.agregar_tarea(
        TareaDefinida(
            nombre="Fabricar mesa",
            tiempo=1,
            unidad_trabajo=UnidadTrabajo("Banco", 10, 1, 1),
            colaboradores_requeridos=[colaborador],
            habilidades_requeridas=[],
        )
    )

    sistema.agregar_elemento(madera, 10)
    sistema.agregar_elemento(mesa)

    for identificador in (1, 2):
        sistema.crear_solicitud(
            Solicitud(
                identificador,
                "Deposito",
                mesa,
                2,
            )
        )

    assert len(sistema.cola_solicitudes) == 2
    assert sistema.cola_solicitudes.ver_primero() == 1

    assert sistema.procesar_siguiente_solicitud() is True

    assert sistema.obtener_solicitud_por_id(1).estado == "planificada"
    assert sistema.obtener_solicitud_por_id(2).estado == "creada"
    assert len(sistema.cola_solicitudes) == 2
    assert sistema.cola_solicitudes.ver_primero() == 1

    sistema.iniciar_produccion(1)
    assert sistema.fabricar_siguiente_producto(1) == (mesa, 2)
    fin_primera_solicitud = sistema.obtener_fin_estimado(1)
    assert sistema.finalizar_produccion(1) is True
    assert sistema.cola_solicitudes.ver_primero() == 2

    assert sistema.procesar_siguiente_solicitud() is True

    assert sistema.obtener_solicitud_por_id(2).estado == "planificada"
    assert len(sistema.cola_solicitudes) == 1
    inicio_segunda = sistema.obtener_programacion_produccion(2)[mesa][0].inicio
    assert inicio_segunda >= fin_primera_solicitud
    sistema.iniciar_produccion(2)
    assert sistema.fabricar_siguiente_producto(2) == (mesa, 2)
    assert sistema.finalizar_produccion(2) is True
    assert len(sistema.cola_solicitudes) == 0
    assert sistema.inventario.obtener_stock(madera) == {
        "actual": 6,
        "reservado": 0,
    }

    assert sistema.procesar_siguiente_solicitud() is False

def test_solicitud_no_se_quita_de_la_cola_si_no_puede_planificarse():
    sistema = SistemaMRP()
    madera = Insumo("Madera", "unidad", 5)
    mesa = Producto("Mesa", "unidad", 1)
    mesa.agregar_a_BOM(ComponenteBOM(madera, 1))
    proceso = ProcesoManufactura(mesa)
    proceso.agregar_tarea(
        TareaDefinida(
            "Fabricar mesa",
            1,
            None,
            [],
            [],
        )
    )
    sistema.agregar_elemento(madera, 0)
    sistema.agregar_elemento(mesa)
    sistema.crear_solicitud(Solicitud(1, "Deposito", mesa, 2))

    assert sistema.procesar_siguiente_solicitud() is False
    assert len(sistema.cola_solicitudes) == 1
    assert sistema.cola_solicitudes.ver_primero() == 1
    assert sistema.obtener_solicitud_por_id(1).estado == "creada"

    sistema.inventario.agregar_stock(madera, 2)
    assert sistema.procesar_siguiente_solicitud() is True
    assert sistema.cola_solicitudes.ver_primero() == 1
    assert sistema.obtener_solicitud_por_id(1).estado == "planificada"
    sistema.iniciar_produccion(1)
    assert sistema.fabricar_siguiente_producto(1) == (mesa, 2)
    assert sistema.finalizar_produccion(1) is True
    assert len(sistema.cola_solicitudes) == 0
