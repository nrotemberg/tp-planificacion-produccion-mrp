import pickle
from src.clases_auxiliares import ColaFIFO
from src.manufactura import Colaborador, UnidadTrabajo, PeriodoOperacion
from src.excepciones import EstadoSolicitudError, TipoInvalidoError
from src.bom import GestorBOM
from src.inventario import Inventario
from src.solicitudes import Solicitud


class SistemaMRP:
    def __init__(self):
        self.elementos_produccion = {}
        self.colaboradores = []
        self.unidades_trabajo = []
        self.solicitudes = {}
        self.cola_solicitudes = ColaFIFO()
        self.inventario = Inventario()
        self.bom = GestorBOM()
        self.planes_materiales = {}
        self._periodos_solicitudes = {}

    def guardar_pickle(self, ruta):
        with open(ruta, "wb") as archivo:
            pickle.dump(self, archivo)

    @classmethod
    def cargar_pickle(cls, ruta):
        with open(ruta, "rb") as archivo:
            sistema = pickle.load(archivo)
        if not isinstance(sistema, cls):
            raise TypeError("El archivo no contiene un SistemaMRP")
        return sistema

    def agregar_elemento(self, elemento, stock_actual=0, stock_reservado=0):
        if elemento.nombre in self.elementos_produccion:
            return False
        self.elementos_produccion[elemento.nombre] = elemento
        self.inventario.registrar(elemento, stock_actual, stock_reservado)
        return True

    def crear_orden_fabricacion(self, id, articulo, cantidad, **parametros):
        solicitante = parametros.pop("solicitante", None)
        solicitud = Solicitud(id, solicitante, articulo, cantidad, **parametros)
        return self.crear_solicitud(solicitud)

    def crear_solicitud(self, solicitud):
        if self.obtener_solicitud_por_id(solicitud.id) is not None:
            return False
        self.solicitudes[solicitud.id] = solicitud
        self.cola_solicitudes.encolar(solicitud.id)
        return True

    def obtener_solicitud_por_id(self, id_solicitud):
        return self.solicitudes.get(id_solicitud)

    def procesar_siguiente_solicitud(self):
        if not self.cola_solicitudes:
            return False

        id_solicitud = self.cola_solicitudes.ver_primero()
        if not self.reservar_recursos(id_solicitud):
            return False

        self.cola_solicitudes.desencolar()
        return True

    def reservar_recursos(self, id_solicitud):
        """Reserva insumos faltantes y subproductos existentes."""
        solicitud = self.obtener_solicitud_por_id(id_solicitud)
        if solicitud is None or solicitud.estado != "creada":
            return False

        faltantes, disponibles = self._obtener_plan_materiales(solicitud)
        if not self.inventario.hay_stock(faltantes):
            return False
        if not self.inventario.hay_stock(disponibles):
            return False

        self.inventario.reservar(faltantes)
        self.inventario.reservar(disponibles)
        self.planes_materiales[solicitud.id] = (faltantes, disponibles)
        solicitud.cambiar_estado()
        return True

    def consumir_stock(self, id_solicitud):
        solicitud = self.obtener_solicitud_por_id(id_solicitud)
        if solicitud is None or solicitud.estado != "en curso":
            return False

        faltantes, disponibles = self.planes_materiales.get(
            solicitud.id,
            self._obtener_plan_materiales(solicitud),
        )
        self.inventario.consumir(faltantes)
        self.inventario.consumir(disponibles)
        self.inventario.agregar_stock(solicitud.producto, solicitud.cantidad)
        solicitud.cambiar_estado()
        self.planes_materiales.pop(solicitud.id, None)
        return True

    def agregar_colaborador(self, colaborador):
        """Registra un colaborador y evita agregar dos veces el mismo objeto."""
        if not isinstance(colaborador, Colaborador):
            raise TipoInvalidoError("El colaborador debe ser una instancia de Colaborador")

        if colaborador in self.colaboradores:
            return False

        self.colaboradores.append(colaborador)
        return True


    def agregar_unidad_trabajo(self, unidad_trabajo):
        """Registra una unidad de trabajo y evita duplicar el mismo objeto."""
        if not isinstance(unidad_trabajo, UnidadTrabajo):
            raise TipoInvalidoError("La unidad de trabajo debe ser una instancia de UnidadTrabajo")

        if unidad_trabajo in self.unidades_trabajo:
            return False

        self.unidades_trabajo.append(unidad_trabajo)
        return True


    def verificar_stock(self, id_solicitud):
        solicitud = self.obtener_solicitud_por_id(id_solicitud)
        if solicitud is None:
            return False
        faltantes, disponibles = self._obtener_plan_materiales(solicitud)
        return self.inventario.hay_stock(faltantes) and self.inventario.hay_stock(
            disponibles
        )

    def iniciar_produccion(self, id_solicitud):
        solicitud = self.obtener_solicitud_por_id(id_solicitud)
        if solicitud is None or solicitud.estado != "planificada":
            return False
        solicitud.cambiar_estado()
        return True
#Desde aca
    def programar_solicitud(self, id_solicitud, periodos):
        """Asocia los períodos de trabajo a una solicitud creada."""
        solicitud = self.obtener_solicitud_por_id(id_solicitud)

        if solicitud is None:
            raise EstadoSolicitudError(
                f"No existe la solicitud '{id_solicitud}'"
            )

        if solicitud.estado != "creada":
            raise EstadoSolicitudError(
                "Solo se puede programar una solicitud creada"
            )

        proceso = getattr(
            solicitud.producto,
            "proceso_manufactura",
            None,
        )

        if proceso is None:
            raise EstadoSolicitudError(
                "El producto no tiene un proceso de manufactura"
            )

        if not isinstance(periodos, list) or any(
            not isinstance(periodo, PeriodoOperacion)
            for periodo in periodos
        ):
            raise TipoInvalidoError(
                "Los períodos deben ser una lista de PeriodoOperacion"
            )

        if not proceso.tareas:
            raise EstadoSolicitudError(
                "El proceso de manufactura no tiene tareas"
            )

        if len(periodos) != len(proceso.tareas):
            raise EstadoSolicitudError(
                "Debe existir un período por cada tarea del proceso"
            )

        for tarea, periodo in zip(proceso.tareas, periodos):
            horas_necesarias = tarea.tiempo * solicitud.cantidad

            if periodo.duracion_horas() < horas_necesarias:
                raise EstadoSolicitudError(
                    f"El período de '{tarea.nombre}' debe cubrir "
                    f"al menos {horas_necesarias} horas"
                )

        proceso.validar_recursos_programados(
            solicitud.cantidad,
            periodos,
        )
        self._validar_conflictos_programacion(
            id_solicitud,
            proceso.tareas,
            periodos,
        )

        # Se guarda después de validar todos los períodos.
        self._periodos_solicitudes[id_solicitud] = tuple(periodos)

    def obtener_periodos_solicitud(self, id_solicitud):
        """Devuelve los períodos programados como una tupla."""
        return self._periodos_solicitudes.get(id_solicitud, ())

    def _validar_conflictos_programacion(
        self,
        id_solicitud,
        tareas,
        periodos,
    ):
        for otro_id, otros_periodos in self._periodos_solicitudes.items():
            if otro_id == id_solicitud:
                continue

            otra_solicitud = self.obtener_solicitud_por_id(otro_id)
            otro_proceso = getattr(
                otra_solicitud.producto,
                "proceso_manufactura",
                None,
            )

            if otro_proceso is None:
                continue

            for tarea, periodo in zip(tareas, periodos):
                for otra_tarea, otro_periodo in zip(
                    otro_proceso.tareas,
                    otros_periodos,
                ):
                    if not periodo.se_solapa_con(otro_periodo):
                        continue

                    if (
                        tarea.unidad_trabajo is not None
                        and tarea.unidad_trabajo is otra_tarea.unidad_trabajo
                    ):
                        raise EstadoSolicitudError(
                            f"La unidad de trabajo "
                            f"'{tarea.unidad_trabajo.nombre}' ya está "
                            "programada en un período superpuesto"
                        )

                    colaboradores_comunes = [
                        colaborador
                        for colaborador in tarea.colaboradores_requeridos
                        if colaborador in otra_tarea.colaboradores_requeridos
                    ]
                    if colaboradores_comunes:
                        colaborador = next(iter(colaboradores_comunes))
                        raise EstadoSolicitudError(
                            f"El colaborador '{colaborador.nombre}' ya está "
                            "programado en un período superpuesto"
                        )

#Hasta aca

    def finalizar_produccion(self, id_solicitud):
        return self.consumir_stock(id_solicitud)

    def detectar_cuello(self):
        pass

    def _obtener_plan_materiales(self, solicitud):
        """Separa lo que hay que fabricar de lo que ya existe en stock.

        `faltantes` contiene los insumos que `hay_stock` verifica para
        fabricar. `disponibles` contiene los subproductos que ya estaban en
        stock y que tambien deben reservarse para no asignarlos a otra
        solicitud.
        """
        return self.bom.calcular_requerimientos(
            solicitud.producto,
            solicitud.cantidad,
            descontar_stock=True,
            inventario=self.inventario,
        )
