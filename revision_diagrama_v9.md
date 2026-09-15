# Revision del Proyecto: Diagrama V9

## Objetivo actual

- Mantener el flujo basico de solicitudes de produccion.
- Simplificar la logica de BOM y stock sin agregar abstracciones innecesarias.
- Separar la explosion de la BOM de las operaciones de inventario.
- Dejar preparada la estructura para agregar Manufactura despues.

## Como leer los porcentajes

| Estado | Significado |
|---|---|
| **100%** | La clase esta completa para su responsabilidad actual y funciona con la implementacion actual. |
| **50% - 99%** | Tiene una parte funcional importante, pero necesita integracion o logica adicional. |
| **10% - 20%** | Tiene estructura y firmas, pero sus metodos todavia estan en `pass`. |

> El alcance funcional actual es BOM, stock y el flujo basico de solicitudes.
> La logica detallada de Manufactura queda reservada para una etapa posterior.

## Resumen rapido

| Clase o modulo | Estado |
|---|---:|
| `Insumo` | **100%** |
| `ComponenteBOM` | **100%** |
| `ElementoProduccion` | **80%** |
| `Producto` | **80%** |
| `Solicitud` | **70%** |
| `bom.py` | **100%** |
| `inventario.py` | **100%** |
| `SistemaMRP` | **75%** |
| `ProcesoManufactura` | **20%** |
| `TareaDefinida` | **10%** |
| `TareaEnCurso` | **10%** |
| `UnidadTrabajo` | **10%** |
| `Colaborador` | **10%** |
| `PeriodoOperacion` | **10%** |

Los porcentajes reflejan el avance hacia el sistema completo del diagrama.
BOM, costos, stock y el flujo basico de solicitudes ya funcionan. La diferencia
restante corresponde principalmente a la integracion con procesos, tareas y
recursos de Manufactura.

## Lectura rapida del codigo

Cada parte tiene una responsabilidad concreta:

```text
Solicitud
    -> dice que producto y cantidad se necesitan

bom.py
    -> calcula los insumos necesarios

Inventario
    -> verifica, reserva y consume el stock

SistemaMRP
    -> conecta todo y cambia el estado de la solicitud
```

Las verificaciones tambien estan separadas por nivel:

```text
ElementoProduccion.hay_stock_suficiente()
    -> verifica un elemento

Inventario.hay_stock()
    -> verifica varios insumos

SistemaMRP.verificar_stock()
    -> verifica una solicitud completa
```

Estas funciones no repiten la misma responsabilidad. Cada una trabaja sobre
un nivel diferente del sistema.

---

## 1. `ElementoProduccion` - 80%

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

- Guarda los datos basicos de un elemento.
- Controla stock total y stock reservado.
- Permite armar e imprimir una BOM.
- Guarda y actualiza el costo.
- Informa si hay stock disponible sin contar el stock ya reservado.

### Falta para llegar al sistema completo

- Relacionarse con un `ProcesoManufactura`.
- Incorporar el costo de manufactura al costo unitario del producto.
- Coordinar el consumo de materiales con tareas reales de produccion.

**Estimacion:** 80%. La base de BOM, stock y costos esta implementada; falta
conectarla con Manufactura.

---

## 2. `Insumo` - 100%

Hereda de `ElementoProduccion`.

### Metodos actuales

- `get_costo()`
- `actualizar_costo()`

### Funciona actualmente

- Representa un material comprado.
- Puede formar parte de una BOM.
- Permite consultar y actualizar su costo.
- Puede ser reservado y consumido por `Inventario`.

### Estado

**100%** para el manejo actual de insumos, BOM y stock.

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
- Permite construir BOM con insumos y con otros productos.

### Estado

**100%** para la estructura BOM actual.

---

## 4. `Producto` - 80%

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
- Puede tener una BOM con varios niveles.

### Falta para llegar al sistema completo

- Tener asociado un `ProcesoManufactura`.
- Sumar al costo el uso de unidades de trabajo y colaboradores.
- Asociar la fabricacion real a un proceso de manufactura.

**Estimacion:** 80%. El BOM, los costos de componentes y la deteccion de ciclos
ya funcionan; falta integrar el proceso de fabricacion.

---

## 5. `Solicitud` - 70%

### Atributos actuales

- `id`
- `solicitante`
- `estado`
- `producto`
- `cantidad`

### Metodos actuales

- `__init__()`
- `cambiar_estado()`

### Estados utilizados

```text
creada -> planificada -> en curso -> finalizada
```

### Funciona actualmente

- Representa una orden de produccion.
- Guarda el producto solicitado y la cantidad.
- Permite cambiar el estado.
- Se sincroniza con `SistemaMRP` para verificar, reservar y consumir stock.
- No permite finalizar directamente una solicitud que no esta en curso.

### Falta para llegar al sistema completo

- Asociar tareas en curso a la solicitud.
- Controlar el avance real de la fabricacion.
- Registrar recursos utilizados y tiempos.
- Validar la finalizacion de tareas de Manufactura.

**Estimacion:** 70%. El ciclo de estados basico y la relacion con stock funcionan,
pero todavia no se controlan tareas ni avances de Manufactura.

---

## 6. `GestorBOM` (`bom.py`) - 100%

### Metodos actuales

- `explotar()`
- `_agregar_requerimientos()`

### Funciona actualmente

- Recorre todos los niveles de una BOM.
- Calcula la cantidad total necesaria de cada insumo.
- Devuelve los requerimientos en un diccionario.
- Suma correctamente cantidades repetidas del mismo insumo.
- Detecta ciclos y evita una recursividad infinita.

### Ejemplo

Si una mesa necesita dos bases y cada base necesita tres unidades de madera:

```text
Mesa x 1
  Base x 2
    Madera x 3
```

La explosion devuelve:

```python
{madera: 6}
```

### Estado

**100%** para la explosion actual de BOM.

La recursividad queda concentrada en esta clase. `SistemaMRP` no necesita
conocer los niveles internos de la BOM.

---

## 7. `inventario.py` - 100%

### Clase actual

- `Inventario`

### Metodos actuales

- `hay_stock()`
- `reservar()`
- `consumir()`

### Funciona actualmente

- Verifica el stock disponible para un conjunto de requerimientos.
- Reserva materiales sin modificar el stock total.
- Consume materiales y reduce el stock reservado.
- Trabaja sobre los requerimientos planos devueltos por `GestorBOM.explotar()`.

### Estado

**100%** para el flujo actual de reserva y consumo de materiales.

La clase es intencionalmente simple: no conoce solicitudes ni estados; solo
administra operaciones de inventario.

---

## 8. `SistemaMRP` - 75%

### Atributos actuales

- `elementos_produccion` (diccionario por nombre)
- `colaboradores`
- `unidades_trabajo`
- `solicitudes` (diccionario por ID)
- `inventario`
- `bom`

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
- `_obtener_requerimientos()`

### Metodos pendientes

- `agregar_colaborador()`: `pass`
- `agregar_unidad_trabajo()`: `pass`
- `detectar_cuello()`: `pass`

### Funciona actualmente

- Administra los elementos de produccion.
- Administra solicitudes por ID.
- Obtiene los requerimientos de una BOM con varios niveles.
- Verifica el stock mediante `Inventario`.
- Reserva materiales mediante `Inventario`.
- Consume materiales mediante `Inventario`.
- Aumenta el stock del producto terminado.
- Actualiza los estados de la solicitud.
- Impide reservar dos veces la misma solicitud.
- Impide consumir una solicitud que no esta en curso.

### Simplificacion realizada

Antes `SistemaMRP` tenia tres recorridos recursivos separados:

```text
_verificar_componentes()
_reservar_componentes()
_consumir_componentes()
```

Ahora el flujo es:

```text
GestorBOM.explotar()
        |
        v
Inventario.hay_stock()
Inventario.reservar()
Inventario.consumir()
```

Esto mantiene el comportamiento original, pero evita repetir la misma logica
recursiva en tres metodos distintos. `GestorBOM` se ocupa de calcular los
materiales; `Inventario` se ocupa de modificar el stock.

Las listas de elementos y solicitudes fueron reemplazadas por diccionarios:

```text
elementos_produccion[nombre] -> elemento
solicitudes[id]               -> solicitud
```

Esto permite buscar directamente por nombre o por ID. Las listas de
colaboradores y unidades de trabajo se mantienen porque esa parte todavía no
esta implementada.

### Falta para llegar al sistema completo

- Administrar colaboradores y unidades de trabajo.
- Ejecutar procesos de Manufactura.
- Asignar tareas y recursos.
- Detectar cuellos de botella reales.
- Coordinar la finalizacion con el estado de las tareas.

**Estimacion:** 75%. El flujo basico de solicitudes, BOM y stock funciona; falta
desarrollar la administracion de recursos y la ejecucion manufacturera.

---

## 9. Manufactura y recursos - pendiente

Estas clases siguen declaradas en `manufactura.py`, pero sus metodos tienen
`pass`:

- `ProcesoManufactura`
- `TareaDefinida`
- `TareaEnCurso`
- `UnidadTrabajo`
- `Colaborador`
- `PeriodoOperacion`

Para no complicar el proyecto, la implementacion futura deberia comenzar con
una lista simple de tareas dentro de `ProcesoManufactura`. Cada tarea podria
guardar su nombre, duracion y recursos necesarios. No hace falta separar
plantillas, ejecuciones y recursos en mas niveles hasta que exista una
necesidad concreta.

Por ahora estas clases no participan del flujo de solicitudes, por lo que no
se mezclan con `Solicitud`, `Inventario` ni `bom.py`.

---

## Como se integran actualmente

1. `Producto` contiene su BOM mediante `ComponenteBOM`.
2. `Solicitud` pide una cantidad de un `Producto`.
3. `SistemaMRP` busca la solicitud.
4. `bom.py` explota la BOM y calcula los insumos necesarios.
5. `Inventario` verifica y reserva los materiales.
6. La solicitud pasa de `creada` a `planificada`.
7. La solicitud pasa a `en curso`.
8. `Inventario` consume los materiales.
9. Se agrega la cantidad fabricada al stock del producto.
10. La solicitud pasa a `finalizada`.

## Flujo actual

```text
crear solicitud
      |
      v
    creada
      |
      | verificar BOM y reservar stock
      v
  planificada
      |
      | iniciar produccion
      v
   en curso
      |
      | consumir stock y generar producto
      v
  finalizada
```

## Como se integraria Manufactura en el futuro

1. `Producto` tendria un `ProcesoManufactura` con sus tareas.
2. `Solicitud` pediria una cantidad de un `Producto`.
3. `SistemaMRP` verificaria y reservaria la BOM.
4. El proceso de Manufactura ejecutaria sus tareas.
5. `UnidadTrabajo` y `Colaborador` aportarian capacidad, disponibilidad y costos.
6. `SistemaMRP` consumiria los insumos y cerraria la solicitud solo cuando las
   tareas estuvieran completas.

## Conclusion

La implementacion actual mantiene el flujo original, pero reduce la
responsabilidad de `SistemaMRP`. La BOM se recorre una sola vez en `bom.py` y
las operaciones de stock se concentran en `Inventario`.

El resultado es un codigo mas simple de seguir:

```text
SistemaMRP
    -> GestorBOM.explotar()
    -> Inventario.hay_stock()
    -> Inventario.reservar()
    -> Inventario.consumir()
```

La parte de Elementos, BOM, stock y solicitudes ya permite ejecutar el flujo
basico completo. Manufactura sigue preparada como siguiente etapa, pero no se
agregan niveles ni clases nuevas hasta que exista una necesidad concreta.
