from src.elementos import ComponenteBOM, Insumo, Producto
from src.solicitudes import Solicitud
from src.SysMRP_simple import SistemaMRP


def crear_sistema():
    madera = Insumo("Madera", "unidad", 10, 0, 5)
    mesa = Producto("Mesa", "unidad", 0, 0, 1)
    mesa.agregar_a_BOM(ComponenteBOM(madera, 2))
    solicitud = Solicitud(1, "Deposito", "creada", mesa, 2)
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
    solicitud = Solicitud(1, "Deposito", "creada", mesa, 2)
    sistema = SistemaMRP()
    sistema.crear_solicitud(solicitud)

    assert sistema.reservar_recursos(1) is True
    assert madera.stock_reservado == 12


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
