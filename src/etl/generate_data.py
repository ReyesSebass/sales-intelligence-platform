# src/etl/generate_data.py
import pandas as pd
import numpy as np
from faker import Faker
from datetime import date, timedelta
import random
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.config import DATA_RAW

# Configuración de semilla para reproducibilidad
# Esto garantiza que los datos sean siempre los mismos al regenerarlos
fake = Faker('es_MX')
Faker.seed(42)
np.random.seed(42)
random.seed(42)

# ── CONFIGURACIÓN GENERAL ───────────────────────────────────────────────────
N_CLIENTES  = 500
N_PRODUCTOS = 100
N_VENDEDORES = 20
N_VENTAS    = 50000
FECHA_INICIO = date(2023, 1, 1)
FECHA_FIN    = date(2024, 12, 31)

REGIONES = ['Norte', 'Sur', 'Este', 'Oeste', 'Centro']
ZONAS    = ['Zona A', 'Zona B', 'Zona C', 'Zona D']

SEGMENTOS_CLIENTE = ['Corporativo', 'PYME', 'Personal']

CATEGORIAS = {
    'Electrónica':    ['Laptops', 'Smartphones', 'Tablets', 'Accesorios'],
    'Oficina':        ['Mobiliario', 'Papelería', 'Impresoras'],
    'Hogar':          ['Electrodomésticos', 'Decoración', 'Cocina'],
    'Ropa':           ['Casual', 'Formal', 'Deportiva'],
    'Alimentos':      ['Bebidas', 'Snacks', 'Frescos'],
    'Herramientas':   ['Manuales', 'Eléctricas', 'Seguridad'],
    'Deportes':       ['Equipos', 'Ropa deportiva', 'Suplementos'],
    'Salud':          ['Medicamentos', 'Cuidado personal', 'Vitaminas'],
}

MARCAS = [
    'TechPro', 'HomeStyle', 'SportMax', 'OfficeElite',
    'FoodBest', 'HealthCare', 'ToolMaster', 'FashionLine'
]


# ── GENERADORES ─────────────────────────────────────────────────────────────

def generate_clientes():
    """Genera el dataset de clientes con datos realistas."""
    print("  Generando clientes...")
    clientes = []

    for i in range(1, N_CLIENTES + 1):
        region = random.choice(REGIONES)
        clientes.append({
            'ClienteID':     i,
            'Nombre':        fake.name(),
            'Email':         fake.email(),
            'Telefono':      fake.phone_number(),
            'Ciudad':        fake.city(),
            'Region':        region,
            'Segmento':      random.choice(SEGMENTOS_CLIENTE),
            'FechaRegistro': fake.date_between(
                                start_date=date(2020, 1, 1),
                                end_date=FECHA_INICIO
                             ),
        })

    return pd.DataFrame(clientes)


def generate_productos():
    """Genera el dataset de productos con precios y costos realistas."""
    print("  Generando productos...")
    productos = []

    for i in range(1, N_PRODUCTOS + 1):
        categoria    = random.choice(list(CATEGORIAS.keys()))
        subcategoria = random.choice(CATEGORIAS[categoria])
        costo        = round(random.uniform(10, 800), 2)
        margen       = random.uniform(0.20, 0.60)
        precio       = round(costo * (1 + margen), 2)

        productos.append({
            'ProductoID':    i,
            'Nombre':        f"{random.choice(MARCAS)} {subcategoria} {fake.bothify('??-###')}",
            'Categoria':     categoria,
            'SubCategoria':  subcategoria,
            'Marca':         random.choice(MARCAS),
            'CostoUnitario': costo,
            'PrecioVenta':   precio,
        })

    return pd.DataFrame(productos)


def generate_vendedores():
    """Genera el dataset de vendedores con regiones asignadas."""
    print("  Generando vendedores...")
    vendedores = []

    for i in range(1, N_VENDEDORES + 1):
        region = random.choice(REGIONES)
        vendedores.append({
            'VendedorID':   i,
            'Nombre':       fake.name(),
            'Email':        fake.company_email(),
            'Region':       region,
            'Zona':         random.choice(ZONAS),
            'FechaIngreso': fake.date_between(
                                start_date=date(2018, 1, 1),
                                end_date=FECHA_INICIO
                            ),
        })

    return pd.DataFrame(vendedores)


def generate_tiempo():
    """
    Genera la dimensión tiempo con todos los días entre
    FECHA_INICIO y FECHA_FIN. Incluye atributos útiles para
    análisis en Power BI.
    """
    print("  Generando dimensión tiempo...")
    fechas = []
    delta  = FECHA_FIN - FECHA_INICIO

    MESES_ES = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }

    DIAS_ES = {
        0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves',
        4: 'Viernes', 5: 'Sábado', 6: 'Domingo'
    }

    for i in range(delta.days + 1):
        fecha = FECHA_INICIO + timedelta(days=i)
        fechas.append({
            'TiempoID':      int(fecha.strftime('%Y%m%d')),
            'Fecha':         fecha,
            'Anio':          fecha.year,
            'Trimestre':     (fecha.month - 1) // 3 + 1,
            'Mes':           fecha.month,
            'NombreMes':     MESES_ES[fecha.month],
            'Semana':        fecha.isocalendar()[1],
            'DiaSemana':     DIAS_ES[fecha.weekday()],
            'EsFinDeSemana': fecha.weekday() >= 5,
        })

    return pd.DataFrame(fechas)


def generate_ventas(df_clientes, df_productos, df_vendedores, df_tiempo):
    """
    Genera 50,000 transacciones de ventas con patrones realistas:
    - Estacionalidad (más ventas en Nov/Dic)
    - Tendencia de crecimiento año a año
    - Descuentos variables por segmento
    """
    print("  Generando ventas (50,000 registros)...")

    # Pesos de estacionalidad por mes
    # Más ventas en Noviembre y Diciembre (temporada alta)
    pesos_mes = {
        1: 0.06, 2: 0.05, 3: 0.07, 4: 0.07,
        5: 0.08, 6: 0.07, 7: 0.07, 8: 0.08,
        9: 0.08, 10: 0.09, 11: 0.11, 12: 0.12
    }

    # Filtra fechas y asigna pesos de estacionalidad
    df_t = df_tiempo.copy()
    df_t['peso'] = df_t['Mes'].map(pesos_mes)

    # Normaliza los pesos
    df_t['peso'] = df_t['peso'] / df_t['peso'].sum()

    # Selecciona fechas con probabilidad estacional
    fechas_ventas = df_t.sample(
        n=N_VENTAS,
        weights='peso',
        replace=True,
        random_state=42
    )

    ventas = []
    for i in range(1, N_VENTAS + 1):
        fila_tiempo  = fechas_ventas.iloc[i - 1]
        producto     = df_productos.sample(1).iloc[0]
        cliente      = df_clientes.sample(1).iloc[0]
        vendedor     = df_vendedores.sample(1).iloc[0]

        cantidad     = random.randint(1, 20)
        precio       = producto['PrecioVenta']
        costo        = producto['CostoUnitario']

        # Descuento mayor para corporativos
        if cliente['Segmento'] == 'Corporativo':
            descuento = round(random.uniform(0.05, 0.20), 2)
        elif cliente['Segmento'] == 'PYME':
            descuento = round(random.uniform(0.02, 0.10), 2)
        else:
            descuento = round(random.uniform(0.00, 0.05), 2)

        ingreso  = round(cantidad * precio * (1 - descuento), 2)
        costo_t  = round(cantidad * costo, 2)
        ganancia = round(ingreso - costo_t, 2)

        ventas.append({
            'VentaID':        i,
            'TiempoID':       int(fila_tiempo['TiempoID']),
            'ClienteID':      int(cliente['ClienteID']),
            'ProductoID':     int(producto['ProductoID']),
            'VendedorID':     int(vendedor['VendedorID']),
            'Cantidad':       cantidad,
            'PrecioUnitario': precio,
            'Descuento':      descuento,
            'CostoTotal':     costo_t,
            'IngresoTotal':   ingreso,
            'Ganancia':       ganancia,
        })

        # Muestra progreso cada 10,000 registros
        if i % 10000 == 0:
            print(f"    → {i:,} registros generados...")

    return pd.DataFrame(ventas)


# ── EJECUCIÓN PRINCIPAL ──────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🚀 Iniciando generación de datos sintéticos...\n")

    # Genera cada dataset
    df_clientes  = generate_clientes()
    df_productos = generate_productos()
    df_vendedores = generate_vendedores()
    df_tiempo    = generate_tiempo()
    df_ventas    = generate_ventas(
                        df_clientes,
                        df_productos,
                        df_vendedores,
                        df_tiempo
                   )

    # Guarda los datasets en data/raw/
    os.makedirs(DATA_RAW, exist_ok=True)

    df_clientes.to_csv(f"{DATA_RAW}/clientes.csv",   index=False)
    df_productos.to_csv(f"{DATA_RAW}/productos.csv", index=False)
    df_vendedores.to_csv(f"{DATA_RAW}/vendedores.csv", index=False)
    df_tiempo.to_csv(f"{DATA_RAW}/tiempo.csv",       index=False)
    df_ventas.to_csv(f"{DATA_RAW}/ventas.csv",       index=False)

    print("\n✅ Archivos CSV guardados en data/raw/")
    print(f"  → clientes.csv   : {len(df_clientes):,} registros")
    print(f"  → productos.csv  : {len(df_productos):,} registros")
    print(f"  → vendedores.csv : {len(df_vendedores):,} registros")
    print(f"  → tiempo.csv     : {len(df_tiempo):,} registros")
    print(f"  → ventas.csv     : {len(df_ventas):,} registros")
    print("\n🎉 Generación de datos completada exitosamente")