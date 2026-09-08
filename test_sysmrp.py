"""
TEST - MANEJO DE STOCK Y BOM
Inicio: 100 madera, 100 clavos, 0 planchas, 0 mesas
"""

from main import ElementoProduccion, Insumo, Producto, Solicitud
from SysMRP_simple import SysMRP

# =====================================================================
# SETUP
# =====================================================================

sistema = SysMRP()

# Insumos: 100 madera, 100 clavos
madera = Insumo("madera", "m2", stock_total=100, stock_reservado=0, costo=10.0)
clavos = Insumo("clavos", "kg", stock_total=100, stock_reservado=0, costo=2.0)

sistema.agregar_elemento(madera)
sistema.agregar_elemento(clavos)

# Plancha: 2 madera + 5 clavos
plancha = Producto("plancha", "u", stock_total=0, stock_reservado=0, costo=30.0)
plancha.construir_bom_manual(madera, 2)
plancha.construir_bom_manual(clavos, 5)
sistema.agregar_elemento(plancha)

# Mesa: 2 plancha + 10 clavos
mesa = Producto("mesa", "u", stock_total=0, stock_reservado=0, costo=80.0)
mesa.construir_bom_manual(plancha, 2)
mesa.construir_bom_manual(clavos, 10)
sistema.agregar_elemento(mesa)

# =====================================================================
# EJECUCION
# =====================================================================

print("\n--- INICIO: Stock inicial ---")
ElementoProduccion.imprimir_stock([madera, clavos, plancha, mesa])

print("\n--- STEP 1: Crear solicitud para 1 mesa ---")
solicitud = Solicitud("SOL1", mesa, 1)
sistema.crear_solicitud(solicitud)

print("BOM de la mesa:")
mesa.imprimir_bom()

print("\n--- STEP 2: Reservar ---")
sistema.reservar_recursos("SOL1")
ElementoProduccion.imprimir_stock([madera, clavos, plancha, mesa])

print("\n--- STEP 3: Consumir stock ---")
sistema.consumir_stock("SOL1")
ElementoProduccion.imprimir_stock([madera, clavos, plancha, mesa])

print("\n--- VERIFICACION: Stock final ---")
ElementoProduccion.imprimir_stock([madera, clavos, plancha, mesa])

print("\nEsperado:")
print("Nombre       | Cantidad | Reservada")
print("-" * 40)
print("madera       |       96 |         0")
print("clavos       |       80 |         0")
print("plancha      |        0 |         0")
print("mesa         |        1 |         0")

print("\n--- BOM COMPLETO ---")
print("\nMESA:")
mesa.imprimir_bom()

print("\nPLANCHA:")
plancha.imprimir_bom()
