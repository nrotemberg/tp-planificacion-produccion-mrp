import sys
from pathlib import Path


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.elementos import ComponenteBOM, Insumo, Producto
from src.solicitudes import Solicitud
from src.SysMRP_simple import SistemaMRP
from src.bom import GestorBOM


def crear_ranger_ejemplo():
    """Construye una BOM pequena pero representativa de una Ranger."""
    aluminio = Insumo("Aluminio", "kg", 200, 0, 5)
    acero = Insumo("Acero", "kg", 300, 0, 8)
    goma = Insumo("Goma", "unidad", 100, 0, 12)
    tela = Insumo("Tela", "m2", 100, 0, 10)
    vidrio = Insumo("Vidrio", "unidad", 50, 0, 15)

    bloque_motor = Producto("Bloque motor", "unidad", 0, 0, 1)
    bloque_motor.agregar_a_BOM(ComponenteBOM(aluminio, 18))
    bloque_motor.agregar_a_BOM(ComponenteBOM(acero, 6))

    motor_v6 = Producto("Motor V6", "unidad", 4, 0, 1)
    motor_v6.agregar_a_BOM(ComponenteBOM(bloque_motor, 1))
    motor_v6.agregar_a_BOM(ComponenteBOM(acero, 4))

    chasis = Producto("Chasis", "unidad", 0, 0, 1)
    chasis.agregar_a_BOM(ComponenteBOM(acero, 35))
    chasis.agregar_a_BOM(ComponenteBOM(aluminio, 8))

    interior = Producto("Interior", "unidad", 0, 0, 1)
    interior.agregar_a_BOM(ComponenteBOM(tela, 12))
    interior.agregar_a_BOM(ComponenteBOM(vidrio, 6))

    ranger = Producto("Ranger", "unidad", 0, 0, 1)
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
    madera = Insumo("Madera", "unidad", 10, 0, 5)
    mesa = Producto("Mesa", "unidad", 0, 0, 1)
    mesa.agregar_a_BOM(ComponenteBOM(madera, 2))
    solicitud = Solicitud(1, "Deposito", mesa, 2)
    sistema = SistemaMRP()
    sistema.agregar_elemento(madera)
    sistema.agregar_elemento(mesa)
    sistema.crear_solicitud(solicitud)
    return sistema, solicitud, madera, mesa


def test_agregar_elementos():
    sistema = SistemaMRP()
    madera = Insumo("Madera", "unidad", 10, 0, 5)

    assert sistema.agregar_elemento(madera) is True
    assert sistema.elementos_produccion == {"Madera": madera}


def test_crear_y_obtener_solicitud_por_id():
    sistema, solicitud, _, _ = crear_sistema()

    assert sistema.obtener_solicitud_por_id(1) is solicitud
    assert sistema.obtener_solicitud_por_id(99) is None
    assert sistema.crear_solicitud(solicitud) is False


def test_verificar_y_reservar_stock():
    sistema, solicitud, madera, _ = crear_sistema()

    assert sistema.verificar_stock(1) is True
    assert sistema.reservar_recursos(1) is True
    assert madera.stock_reservado == 4
    assert solicitud.estado == "planificada"


def test_no_reservar_si_no_hay_stock():
    sistema, _, madera, _ = crear_sistema()
    madera.stock_total = 3

    assert sistema.verificar_stock(1) is False
    assert sistema.reservar_recursos(1) is False
    assert madera.stock_reservado == 0


def test_planificar_es_un_alias_de_reservar_en_el_sistema():
    sistema, _, _, _ = crear_sistema()

    assert sistema.planificar_solicitud(1) is True


def test_iniciar_y_finalizar_produccion_consumen_stock():
    sistema, solicitud, madera, mesa = crear_sistema()
    sistema.reservar_recursos(1)

    assert sistema.iniciar_produccion(1) is True
    assert solicitud.estado == "en curso"
    assert sistema.finalizar_produccion(1) is True
    assert solicitud.estado == "finalizada"
    assert madera.stock_total == 6
    assert madera.stock_reservado == 0
    assert mesa.stock_total == 2


def test_bom_anidada_reserva_el_stock_de_los_insumos():
    madera = Insumo("Madera", "unidad", 20, 0, 5)
    base = Producto("Base", "unidad", 0, 0, 1)
    mesa = Producto("Mesa", "unidad", 0, 0, 1)
    base.agregar_a_BOM(ComponenteBOM(madera, 3))
    mesa.agregar_a_BOM(ComponenteBOM(base, 2))
    solicitud = Solicitud(1, "Deposito", mesa, 2)
    sistema = SistemaMRP()
    sistema.crear_solicitud(solicitud)

    assert sistema.reservar_recursos(1) is True
    assert madera.stock_reservado == 12


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
        "    `-- Vidrio x 60\n"
    )


def test_calcular_requerimientos_agrega_elementos_repetidos():
    ranger = crear_ranger_ejemplo()
    insumos, _ = GestorBOM().calcular_requerimientos(ranger, 10)

    # Verificamos que se agreguen las cantidades totales por insumo (por nombre)
    cantidades_por_nombre = {insumo.nombre: cant for insumo, cant in insumos.items()}
    assert cantidades_por_nombre["Aluminio"] == 260
    assert cantidades_por_nombre["Acero"] == 450
    assert cantidades_por_nombre["Goma"] == 40
    assert cantidades_por_nombre["Tela"] == 120
    assert cantidades_por_nombre["Vidrio"] == 60


def test_bom_considera_stock_de_subproducto_intermedio():
    aluminio = Insumo("Aluminio", "unidad", 20, 0, 5)
    v6 = Producto("V6", "unidad", 4, 0, 1)
    ranger = Producto("Ranger", "unidad", 0, 0, 1)
    v6.agregar_a_BOM(ComponenteBOM(aluminio, 2))
    ranger.agregar_a_BOM(ComponenteBOM(v6, 1))
    solicitud = Solicitud(1, "Deposito", ranger, 10)
    sistema = SistemaMRP()
    sistema.crear_solicitud(solicitud)

    bom_original = list(ranger.lista_elementos_bom)
    bom_v6_original = list(v6.lista_elementos_bom)
    faltantes, _ = sistema._obtener_plan_materiales(solicitud)
    assert faltantes == {aluminio: 12}
    assert ranger.lista_elementos_bom == bom_original
    assert v6.lista_elementos_bom == bom_v6_original


def test_verificar_stock_considera_subproductos_y_requerimientos_netos():
    aluminio = Insumo("Aluminio", "unidad", 12, 0, 5)
    v6 = Producto("V6", "unidad", 4, 0, 1)
    ranger = Producto("Ranger", "unidad", 0, 0, 1)
    v6.agregar_a_BOM(ComponenteBOM(aluminio, 2))
    ranger.agregar_a_BOM(ComponenteBOM(v6, 1))
    solicitud = Solicitud(1, "Deposito", ranger, 10)
    sistema = SistemaMRP()
    sistema.crear_solicitud(solicitud)

    # Los 4 V6 disponibles cubren parte de la demanda: solo hacen falta
    # materiales para fabricar los 6 V6 restantes (12 unidades de aluminio).
    assert sistema.verificar_stock(1) is True

    aluminio.stock_total = 11
    assert sistema.verificar_stock(1) is False


def test_reservar_y_consumir_stock_intermedio():
    aluminio = Insumo("Aluminio", "unidad", 20, 0, 5)
    v6 = Producto("V6", "unidad", 4, 0, 1)
    ranger = Producto("Ranger", "unidad", 0, 0, 1)
    v6.agregar_a_BOM(ComponenteBOM(aluminio, 2))
    ranger.agregar_a_BOM(ComponenteBOM(v6, 1))
    solicitud = Solicitud(1, "Deposito", ranger, 10)
    sistema = SistemaMRP()
    sistema.crear_solicitud(solicitud)

    assert sistema.reservar_recursos(1) is True
    assert v6.stock_reservado == 4
    assert aluminio.stock_reservado == 12

    sistema.iniciar_produccion(1)
    assert sistema.finalizar_produccion(1) is True
    assert v6.stock_total == 0
    assert v6.stock_reservado == 0


def test_no_se_puede_finalizar_solicitud_sin_iniciarla():
    sistema, _, _, _ = crear_sistema()

    assert sistema.finalizar_produccion(1) is False


def test_metodos_rechazan_id_inexistente():
    sistema = SistemaMRP()

    assert sistema.verificar_stock(99) is False
    assert sistema.reservar_recursos(99) is False
    assert sistema.consumir_stock(99) is False
    assert sistema.iniciar_produccion(99) is False
    assert sistema.finalizar_produccion(99) is False
