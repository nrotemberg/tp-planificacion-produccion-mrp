from datetime import datetime, timedelta
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
        self._cantidades_a_fabricar = {}
        self._periodos_efectivos = {}
        self._planes_produccion = {}
        self._programaciones_produccion = {}
        self._finalizaciones_estimadas = {}
        self._fabricaciones_realizadas = {}
        self._tareas_fabricacion = {}

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
        solicitud = self.obtener_solicitud_por_id(id_solicitud)
        if solicitud is None:
            return False
        if solicitud.estado == "creada":
            return self.reservar_recursos(id_solicitud)
        return solicitud.estado in ("planificada", "en curso")

    def reservar_recursos(self, id_solicitud):
        solicitud = self.obtener_solicitud_por_id(id_solicitud)

        if solicitud is None or solicitud.estado != "creada":
            return False

        plan = self.bom.calcular_plan(solicitud.producto, solicitud.cantidad, self.inventario,)

        faltantes = plan["insumos"]
        disponibles = plan["desde_stock"]

        desde_stock = disponibles.get(solicitud.producto, 0)
        cantidad_a_fabricar = solicitud.cantidad - desde_stock

        requerimientos = dict(faltantes)

        for elemento, cantidad in disponibles.items():
            requerimientos[elemento] = (requerimientos.get(elemento, 0) + cantidad)

        if not self.inventario.hay_stock(requerimientos):
            return False

        solicitud.inicio_planificacion = datetime.now().astimezone()

        # Validar manufactura antes de modificar las reservas.
        programacion = self._calcular_programacion_plan(solicitud, plan,)

        self.inventario.reservar(requerimientos)

        self.planes_materiales[solicitud.id] = (faltantes,disponibles,)
        self._planes_produccion[solicitud.id] = plan
        self._cantidades_a_fabricar[solicitud.id] = cantidad_a_fabricar
        self._programaciones_produccion[solicitud.id] = programacion
        self._finalizaciones_estimadas[solicitud.id] = max(
            (
                periodo.fin
                for periodos in programacion.values()
                for periodo in periodos
            ),
            default=solicitud.inicio_planificacion,
        )

        # Mantener la consulta existente del producto principal.
        self._periodos_efectivos[solicitud.id] = programacion.get(solicitud.producto, (),)

        solicitud.cambiar_estado()
        return True

    def fabricar_siguiente_producto(self, id_solicitud):
        """Simula la siguiente fabricación del plan y actualiza el inventario."""
        solicitud = self.obtener_solicitud_por_id(id_solicitud)

        if solicitud is None or solicitud.estado != "en curso":
            raise EstadoSolicitudError(
                "La solicitud debe estar en curso"
            )

        plan = self.obtener_plan_produccion(id_solicitud)

        realizados = self._fabricaciones_realizadas.setdefault(
            id_solicitud,
            set(),
        )

        producto = next(
            (
                elemento
                for elemento in plan["orden_fabricacion"]
                if elemento not in realizados
            ),
            None,
        )

        # No quedan productos pendientes.
        if producto is None:
            return None

        cantidad = plan["a_fabricar"][producto]

        # Componentes directos consumidos por esta fabricación.
        requerimientos = {}

        for componente in producto.lista_elementos_bom:
            elemento = componente.elemento_produccion

            requerimientos[elemento] = (
                requerimientos.get(elemento, 0)
                + componente.cantidad * cantidad
            )

        # Comprobar todos los componentes antes de ejecutar tareas.
        for elemento, necesaria in requerimientos.items():
            stock = self.inventario.obtener_stock(elemento)

            if (
                stock["actual"] < necesaria
                or stock["reservado"] < necesaria
            ):
                raise EstadoSolicitudError(
                    f"No hay suficientes unidades reservadas "
                    f"de '{elemento.nombre}' para fabricar "
                    f"'{producto.nombre}'"
                )

        programacion = self.obtener_programacion_produccion(
            id_solicitud
        )
        periodos = programacion[producto]
        proceso = producto.proceso_manufactura

        tareas = proceso.iniciar_proceso(
            cantidad,
            list(periodos),
        )

        self._tareas_fabricacion.setdefault(
            id_solicitud,
            {},
        )[producto] = tuple(tareas)

        for tarea in tareas:
            tarea.actualizar_estado("en_curso")
            tarea.finalizar()

        # Transformar los componentes en el producto fabricado.
        self.inventario.consumir(requerimientos)
        self.inventario.agregar_stock(producto, cantidad)

        # La producción nueva queda reservada para esta solicitud.
        self.inventario.reservar({producto: cantidad})

        realizados.add(producto)

        return producto, cantidad

    def obtener_historial_tareas(self):
        """Devuelve las ejecuciones de tareas registradas durante la sesión."""
        historial = []

        for id_solicitud, productos in self._tareas_fabricacion.items():
            for producto, tareas in productos.items():
                for tarea in tareas:
                    historial.append(
                        {
                            "solicitud": id_solicitud,
                            "producto": producto,
                            "tarea": tarea,
                            "estado": tarea.estado,
                        }
                    )

        return historial

    def consumir_stock(self, id_solicitud):
        """Entrega el pedido cuando terminaron todas sus fabricaciones."""
        solicitud = self.obtener_solicitud_por_id(id_solicitud)

        if solicitud is None or solicitud.estado != "en curso":
            return False

        if id_solicitud not in self.planes_materiales:
            raise EstadoSolicitudError(
                "La solicitud no tiene un plan reservado"
            )

        plan = self.obtener_plan_produccion(id_solicitud)

        realizados = self._fabricaciones_realizadas.get(
            id_solicitud,
            set(),
        )

        if any(
            producto not in realizados
            for producto in plan["orden_fabricacion"]
        ):
            raise EstadoSolicitudError(
                "Todavía hay productos pendientes de fabricación"
            )

        producto = solicitud.producto
        stock = self.inventario.obtener_stock(producto)

        if (
            stock["actual"] < solicitud.cantidad
            or stock["reservado"] < solicitud.cantidad
        ):
            raise EstadoSolicitudError(
                "No hay suficientes productos reservados para entregar"
            )

        self.inventario.consumir(
            {producto: solicitud.cantidad}
        )

        solicitud.cambiar_estado()
        self.planes_materiales.pop(id_solicitud)
        if (
            self.cola_solicitudes
            and self.cola_solicitudes.ver_primero() == id_solicitud
        ):
            self.cola_solicitudes.desencolar()

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

    def finalizar_produccion(self, id_solicitud):
        return self.consumir_stock(id_solicitud)

    def detectar_cuello(self):
        """Devuelve hasta tres unidades ordenadas por horas ocupadas.

        Cada resultado contiene la unidad y la suma de las duraciones de sus
        períodos ocupados. Las unidades sin períodos ocupados no se incluyen.
        """
        unidades_con_carga = []

        for unidad in self.unidades_trabajo:
            horas_ocupadas = sum(
                periodo.duracion_horas()
                for periodo in unidad.periodos_ocupados
            )
            if horas_ocupadas > 0:
                unidades_con_carga.append(
                    {
                        "unidad": unidad,
                        "horas_ocupadas": horas_ocupadas,
                    }
                )

        unidades_con_carga.sort(
            key=lambda carga: carga["horas_ocupadas"],
            reverse=True,
        )
        return unidades_con_carga[:3]

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

    def obtener_plan_produccion(self, id_solicitud):
        """Devuelve una copia del plan reservado para la solicitud."""
        if id_solicitud not in self._planes_produccion:
            raise EstadoSolicitudError(
                "La solicitud todavía no tiene un plan de producción"
            )

        plan = self._planes_produccion[id_solicitud]

        return {
            "insumos": dict(plan["insumos"]),
            "desde_stock": dict(plan["desde_stock"]),
            "a_fabricar": dict(plan["a_fabricar"]),
            "orden_fabricacion": tuple(plan["orden_fabricacion"]),
        }

    def calcular_costo_fabricacion(self, id_solicitud):
        """Calcula insumos y operaciones de la fabricación nueva."""
        plan = self.obtener_plan_produccion(id_solicitud)

        costo_insumos = sum(
            elemento.costo_unitario() * cantidad
            for elemento, cantidad in plan["insumos"].items()
        )

        costo_operaciones = sum(
            producto.proceso_manufactura.calcular_costo_operativo()
            * cantidad
            for producto, cantidad in plan["a_fabricar"].items()
        )

        return costo_insumos + costo_operaciones

    def obtener_cantidad_a_fabricar(self, id_solicitud):
        if id_solicitud not in self._cantidades_a_fabricar:
            raise EstadoSolicitudError(
                "La solicitud todavía no tiene un plan"
            )

        return self._cantidades_a_fabricar[id_solicitud]

    def obtener_periodos_produccion(self, id_solicitud):
        return self._periodos_efectivos.get(id_solicitud, ())

    def obtener_programacion_produccion(self, id_solicitud):
        """Devuelve una copia de la programación por producto."""
        if id_solicitud not in self._programaciones_produccion:
            raise EstadoSolicitudError(
                "La solicitud todavía no tiene una programación efectiva"
            )

        programacion = self._programaciones_produccion[id_solicitud]

        return {
            producto: tuple(periodos)
            for producto, periodos in programacion.items()
        }

    def obtener_fin_estimado(self, id_solicitud):
        if id_solicitud not in self._finalizaciones_estimadas:
            raise EstadoSolicitudError(
                "La solicitud todavía no tiene una programación"
            )
        return self._finalizaciones_estimadas[id_solicitud]

    def _calcular_programacion_plan(self, solicitud, plan):
        """Genera períodos automáticos respetando BOM y recursos compartidos."""
        programacion = {}
        ocupaciones = {}

        for recurso in (*self.unidades_trabajo, *self.colaboradores):
            ocupaciones[recurso] = list(recurso.periodos_ocupados)

        for otro_id, registrada in self._programaciones_produccion.items():
            if otro_id == solicitud.id:
                continue
            for producto, periodos in registrada.items():
                for tarea, periodo in zip(
                    producto.proceso_manufactura.tareas,
                    periodos,
                ):
                    for recurso in self._recursos_de_tarea(tarea):
                        ocupaciones.setdefault(recurso, []).append(periodo)

        inicio_solicitud = solicitud.inicio_planificacion

        for producto in plan["orden_fabricacion"]:
            cantidad = plan["a_fabricar"][producto]
            proceso = producto.proceso_manufactura
            if proceso is None or not proceso.tareas:
                raise EstadoSolicitudError(
                    f"El producto '{producto.nombre}' necesita tareas de manufactura"
                )

            fin_componentes = max(
                (
                    periodo.fin
                    for componente in producto.lista_elementos_bom
                    for periodo in programacion.get(
                        componente.elemento_produccion,
                        (),
                    )
                ),
                default=inicio_solicitud,
            )
            periodos_por_tarea = {}
            periodos = []

            for tarea in proceso.tareas:
                if any(
                    predecesora not in periodos_por_tarea
                    for predecesora in tarea.subtareas
                ):
                    raise EstadoSolicitudError(
                        f"Las predecesoras de '{tarea.nombre}' "
                        "deben aparecer antes en el proceso"
                    )

                inicio = max(
                    (
                        inicio_solicitud,
                        fin_componentes,
                        *(
                            periodos_por_tarea[predecesora].fin
                            for predecesora in tarea.subtareas
                        ),
                    )
                )
                recursos = self._recursos_de_tarea(tarea)
                duracion = timedelta(hours=tarea.tiempo * cantidad)
                for recurso in recursos:
                    ocupaciones.setdefault(
                        recurso,
                        list(recurso.periodos_ocupados),
                    )

                while True:
                    periodo = PeriodoOperacion(inicio, inicio + duracion)
                    conflictos = [
                        ocupado
                        for recurso in recursos
                        for ocupado in ocupaciones.get(recurso, ())
                        if periodo.se_solapa_con(ocupado)
                    ]
                    if not conflictos:
                        break
                    inicio = min(conflictos, key=lambda ocupado: ocupado.fin).fin

                periodos.append(periodo)
                periodos_por_tarea[tarea] = periodo
                for recurso in recursos:
                    ocupaciones.setdefault(recurso, []).append(periodo)

            proceso.validar_recursos_programados(cantidad, periodos)
            programacion[producto] = tuple(periodos)

        return programacion

    @staticmethod
    def _recursos_de_tarea(tarea):
        recursos = list(tarea.colaboradores_requeridos)
        if tarea.unidad_trabajo is not None:
            recursos.append(tarea.unidad_trabajo)
        return recursos