# Revision del Proyecto: Diagrama V8

## Objetivo actual

- Trabajar primero con **BOM**, costos y stock.
- Dejar preparada la estructura para agregar Manufactura despues.
- Integrar en el futuro Elementos, Solicitudes y Manufactura.

## Como leer los porcentajes

| Estado | Significado |
|---|---|
| **100%** | La clase esta completa para su responsabilidad actual y no depende de logica pendiente para funcionar. |
| **50% - 99%** | Tiene una parte funcional importante, pero necesita integracion o logica adicional. |
| **10% - 20%** | Tiene estructura y firmas, pero sus metodos todavia estan en `pass`. |

> El alcance funcional actual es BOM y stock. La logica de Manufactura queda reservada para una etapa posterior.

## Resumen rapido

| Clase | Estado |
|---|---:|
| `Insumo` | **100%** |
| `ComponenteBOM` | **100%** |
| `ElementoProduccion` | **70%** |
| `Producto` | **65%** |
| `Solicitud` | **55%** |
| `SistemaMRP` | **60%** |
| `ProcesoManufactura` | **20%** |
| `TareaDefinida` | **10%** |
| `TareaEnCurso` | **10%** |
| `UnidadTrabajo` | **10%** |
| `Colaborador` | **10%** |
| `PeriodoOperacion` | **10%** |

Los porcentajes reflejan el avance total hacia el sistema del diagrama. BOM y stock
ya funcionan; la diferencia restante corresponde principalmente a la integracion
con procesos, tareas y recursos de Manufactura.

---

## 1. `ElementoProduccion` - 70%

### Atributos actuales

- `nombre`
- `unidad_medida`
- `stock_total`
- `stock_reservado`
- `costo`
- `lista_elementos_bom`

### Metodos actuales

- `__init__()`
- `set_costo()`
- `hay_stock_suficiente()`
- `construir_bom_manual()`
- `agregar_a_BOM()`
- `imprimir_bom()`
- `imprimir_stock()`
- `costo_unitario()`

### Funciona actualmente

- Guarda datos basicos de un elemento.
- Controla stock total y stock reservado.
- Permite armar e imprimir un BOM.
- Guarda y actualiza el costo.

### Falta para llegar al sistema completo

- Relacionarse con un `ProcesoManufactura`.
- Incorporar el costo de manufactura al costo unitario del producto.
- Coordinar el consumo de materiales con la produccion real.

**Estimacion:** 70%. La base de BOM, stock y costos esta implementada; falta conectarla con Manufactura.

---

## 2. `Insumo` - 100%

Hereda de `ElementoProduccion`.

### Metodos actuales

- `get_costo()`
- `actualizar_costo()`

### Funciona actualmente

- Representa un material comprado.
- Puede formar parte de un BOM.
- Permite consultar y actualizar su costo.

### Estado

**100%** para el manejo actual de insumos, BOM y stock. No necesita participar directamente en Manufactura.

---

## 3. `ComponenteBOM` - 100%

### Atributos actuales

- `elemento_produccion`
- `cantidad`

### Metodos actuales

- `__init__()`
- `validar_cantidad()`

### Funciona actualmente

- Relaciona un elemento con la cantidad necesaria para fabricar otro.
- Valida que la cantidad sea un entero positivo.

### Estado

**100%** para la estructura BOM actual.

---

## 4. `Producto` - 65%

Hereda de `ElementoProduccion`.

### Metodos propios actuales

- `costo_unitario()`
- `detectar_ciclo()`

### Metodos heredados utilizados

- `hay_stock_suficiente()`
- `construir_bom_manual()`
- `agregar_a_BOM()`
- `imprimir_bom()`

### Funciona actualmente

- Puede contener insumos y otros productos en su BOM.
- Calcula el costo de sus componentes.
- Detecta ciclos directos e indirectos.
- Puede ser el producto de una `Solicitud`.

### Falta para llegar al sistema completo

- Tener asociado un `ProcesoManufactura`.
- Sumar al costo el uso de unidades de trabajo y colaboradores.
- Actualizar su stock como resultado de una fabricacion real.
- Coordinar el BOM con las tareas de manufactura.

**Estimacion:** 65%. El BOM y el costo de componentes funcionan, pero falta integrar el proceso de fabricacion.

---

## 5. `Solicitud` - 55%

### Atributos actuales

- `id`
- `solicitante`
- `estado`
- `producto`
- `cantidad`

### Metodos actuales

- `__init__()`
- `cambiar_estado()`

### Funciona actualmente

- Representa una orden de produccion.
- Guarda el producto solicitado y la cantidad.
- Permite cambiar el estado.
- Se sincroniza con `SistemaMRP` para verificar, reservar y consumir stock.

### Falta para llegar al sistema completo

- Asociar tareas en curso a la solicitud.
- Controlar el avance real de la fabricacion.
- Validar que la produccion haya terminado antes de finalizarla.
- Registrar recursos utilizados y tiempos.

**Estimacion:** 55%. La solicitud se sincroniza con stock mediante `SistemaMRP`, pero todavia no controla tareas ni avances de Manufactura.

---

## 6. `SistemaMRP` - 60%

### Atributos actuales

- `elementos_produccion`
- `colaboradores`
- `unidades_trabajo`
- `solicitudes`

### Metodos funcionales actuales

- `__init__()`
- `agregar_elemento()`
- `crear_solicitud()`
- `obtener_solicitud_por_id()`
- `reservar_recursos()`
- `consumir_stock()`
- `planificar_solicitud()`
- `verificar_stock()`
- `iniciar_produccion()`
- `finalizar_produccion()`
- `_verificar_componentes()`
- `_reservar_componentes()`
- `_consumir_componentes()`

### Metodos pendientes

- `agregar_colaborador()`: `pass`
- `agregar_unidad_trabajo()`: `pass`
- `detectar_cuello()`: `pass`

### Funciona actualmente

- Administra los elementos de produccion.
- Administra solicitudes por ID.
- Verifica el stock recursivamente en el BOM.
- Reserva materiales.
- Consume materiales y genera el producto solicitado.
- Actualiza los estados de la solicitud.

### Falta para llegar al sistema completo

- Administrar colaboradores y unidades de trabajo.
- Ejecutar procesos de manufactura.
- Asignar tareas y recursos.
- Detectar cuellos de botella reales.
- Coordinar la finalizacion con el estado de las tareas.

**Estimacion:** 60%. El ciclo BOM y stock funciona; falta desarrollar la administracion de recursos y la ejecucion manufacturera.

---

## 7. `ProcesoManufactura` - 20%

### Estructura definida

- `__init__(producto)`
- `agregar_tarea()`
- `agregar_proceso()`
- `modificar_proceso()`
- `calcular_costo_operativo()`

### Estado actual

**Estructura inicial:** todos los metodos tienen `pass`.

### Falta

- Guardar y ordenar las tareas del proceso.
- Calcular el costo de las tareas.
- Asociarse a un `Producto`.
- Informar a `SistemaMRP` sobre el proceso necesario.

**Estimacion:** 20%. La clase tiene su estructura, pero todavia no ejecuta ninguna logica.

---

## 8. `TareaDefinida` - 10%

### Estructura definida

- `__init__(nombre, tiempo, unidad_trabajo, colaboradores_requeridos, habilidades_requeridas)`
- `agregar_tarea()`
- `costo_operativo()`

### Estado actual

**Estructura inicial:** todos los metodos tienen `pass`.

### Falta

- Guardar la definicion de una tarea.
- Validar tiempo, unidad de trabajo y colaboradores.
- Calcular el costo de la tarea.
- Servir como plantilla para `TareaEnCurso`.

**Estimacion:** 10%. Solo estan definidas la clase y sus firmas de metodos.

---

## 9. `TareaEnCurso` - 10%

### Estructura definida

- `__init__(nombre, tarea_base, estado)`
- `actualizar_estado()`
- `asignar_colaboradores()`
- `asignar_UTs()`

### Estado actual

**Estructura inicial:** todos los metodos tienen `pass`.

### Falta

- Representar una tarea que se esta ejecutando.
- Registrar colaboradores y unidades de trabajo asignados.
- Validar disponibilidad de recursos.
- Informar el avance a la `Solicitud`.

**Estimacion:** 10%. Falta implementar toda la ejecucion y seguimiento de tareas.

---

## 10. `UnidadTrabajo` - 10%

### Estructura definida

- `__init__(nombre, capacidad_max_produccion, costo_fijo, capacidad_colaboradores)`
- `verificar_capacidad()`

### Estado actual

**Estructura inicial:** todos los metodos tienen `pass`.

### Falta

- Controlar capacidad de produccion.
- Administrar periodos de operacion.
- Administrar colaboradores activos.
- Participar en la deteccion de cuellos de botella.

**Estimacion:** 10%. La clase esta declarada, pero no administra capacidad ni disponibilidad.

---

## 11. `Colaborador` - 10%

### Estructura definida

- `__init__(nombre, costo_por_hora, habilidades)`
- `tiene_habilidad()`
- `verificar_disponibilidad()`

### Estado actual

**Estructura inicial:** todos los metodos tienen `pass`.

### Falta

- Guardar habilidades y costo horario.
- Validar si puede realizar una tarea.
- Controlar disponibilidad por periodo.
- Participar en el costo de manufactura.

**Estimacion:** 10%. Falta implementar habilidades, disponibilidad y costos.

---

## 12. `PeriodoOperacion` - 10%

### Estructura definida

- `__init__(inicio, fin)`
- `duracion_horas()`
- `se_solapa_con()`

### Estado actual

**Estructura inicial:** todos los metodos tienen `pass`.

### Falta

- Representar un intervalo de trabajo.
- Calcular su duracion.
- Detectar superposiciones de horarios.
- Ser utilizado por colaboradores y unidades de trabajo.

**Estimacion:** 10%. Solo existe la firma de la clase; falta toda la logica temporal.

---

## Como se integrarian en el futuro

1. **Producto**
   - Tendria un `ProcesoManufactura` con sus `TareaDefinida`.

2. **Solicitud**
   - Pediria una cantidad de un `Producto` y generaria las tareas necesarias.

3. **SistemaMRP**
   - Verificaria y reservaria el BOM, ademas de asignar recursos de manufactura.

4. **TareaEnCurso**
   - Representaria cada tarea ejecutada para una solicitud.

5. **UnidadTrabajo y Colaborador**
   - Aportarian capacidad, disponibilidad y costos.

6. **Finalizacion**
   - `SistemaMRP` consumiria los insumos, actualizaria el producto fabricado y cerraria la `Solicitud` solo cuando las tareas estuvieran completas.

## Conclusion

La parte de Elementos, BOM y stock ya permite realizar el test global de madera, clavos, plancha y mesa.

La integracion con Manufactura todavia no esta implementada. Por eso las
clases tienen distintos porcentajes: algunas ya resuelven por completo su
responsabilidad actual, mientras que otras solo tienen la estructura o el
flujo parcial. Falta agregar la logica que conecte Manufactura con `Producto`,
`Solicitud` y `SistemaMRP`.
