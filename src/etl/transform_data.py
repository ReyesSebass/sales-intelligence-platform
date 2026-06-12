# src/etl/transform_data.py
import pandas as pd
import pyodbc
from sqlalchemy import create_engine
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.config import DB_SERVER, DB_NAME, DATA_PROCESSED


# ── CONEXIÓN ─────────────────────────────────────────────────────────────────

def get_engine():
    """Retorna un engine de SQLAlchemy para conectar con SQL Server."""
    connection_string = (
        f"mssql+pyodbc://@{DB_SERVER}/{DB_NAME}"
        f"?driver=ODBC+Driver+17+for+SQL+Server"
        f"&trusted_connection=yes"
    )
    return create_engine(connection_string)


# ── EXTRACCIÓN ───────────────────────────────────────────────────────────────

def extract_tables():
    """
    Extrae las 5 tablas de SQL Server y las retorna como DataFrames.
    """
    engine = get_engine()

    print("  → Extrayendo FactVentas...")
    df_ventas = pd.read_sql("SELECT * FROM FactVentas", engine)

    print("  → Extrayendo DimClientes...")
    df_clientes = pd.read_sql("SELECT * FROM DimClientes", engine)

    print("  → Extrayendo DimProductos...")
    df_productos = pd.read_sql("SELECT * FROM DimProductos", engine)

    print("  → Extrayendo DimVendedores...")
    df_vendedores = pd.read_sql("SELECT * FROM DimVendedores", engine)

    print("  → Extrayendo DimTiempo...")
    df_tiempo = pd.read_sql("SELECT * FROM DimTiempo", engine)

    return df_ventas, df_clientes, df_productos, df_vendedores, df_tiempo


# ── TRANSFORMACIÓN ───────────────────────────────────────────────────────────

def build_analytical_dataset(df_ventas, df_clientes, df_productos, df_vendedores, df_tiempo):
    """
    Une (join) la tabla de hechos con todas las dimensiones
    para crear una vista plana lista para análisis.
    """
    print("  → Uniendo FactVentas con dimensiones...")

    df = df_ventas.copy()

    # Join con Clientes
    df = df.merge(
        df_clientes[['ClienteID', 'Nombre', 'Region', 'Segmento']],
        on='ClienteID',
        how='left',
        suffixes=('', '_Cliente')
    )
    df = df.rename(columns={
        'Nombre': 'NombreCliente',
        'Region': 'RegionCliente',
        'Segmento': 'SegmentoCliente'
    })

    # Join con Productos
    df = df.merge(
        df_productos[['ProductoID', 'Nombre', 'Categoria', 'SubCategoria', 'Marca']],
        on='ProductoID',
        how='left'
    )
    df = df.rename(columns={'Nombre': 'NombreProducto'})

    # Join con Vendedores
    df = df.merge(
        df_vendedores[['VendedorID', 'Nombre', 'Region', 'Zona']],
        on='VendedorID',
        how='left',
        suffixes=('', '_Vendedor')
    )
    df = df.rename(columns={
        'Nombre': 'NombreVendedor',
        'Region': 'RegionVendedor',
        'Zona': 'ZonaVendedor'
    })

    # Join con Tiempo
    df = df.merge(
        df_tiempo[['TiempoID', 'Fecha', 'Anio', 'Trimestre', 'Mes', 'NombreMes', 'DiaSemana', 'EsFinDeSemana']],
        on='TiempoID',
        how='left'
    )

    return df


def add_calculated_columns(df):
    """
    Agrega columnas calculadas útiles para el análisis:
    - Margen porcentual
    - Indicador de venta con descuento
    - Periodo Año-Mes para agrupaciones
    """
    print("  → Agregando columnas calculadas...")

    # Asegura que Fecha sea tipo datetime
    df['Fecha'] = pd.to_datetime(df['Fecha'])

    df['MargenPorcentaje'] = (df['Ganancia'] / df['IngresoTotal'] * 100).round(2)
    df['TuvoDescuento'] = df['Descuento'] > 0
    df['AnioMes'] = df['Fecha'].dt.strftime('%Y-%m')

    return df


def validate_data(df):
    """
    Validaciones básicas de calidad de datos.
    Imprime un resumen y alerta si hay valores nulos o inconsistencias.
    """
    print("\n📊 Validación de calidad de datos:")
    print(f"  → Total de registros: {len(df):,}")
    print(f"  → Columnas: {len(df.columns)}")

    nulos = df.isnull().sum()
    columnas_con_nulos = nulos[nulos > 0]

    if len(columnas_con_nulos) > 0:
        print("\n  ⚠️ Columnas con valores nulos:")
        for col, count in columnas_con_nulos.items():
            print(f"    - {col}: {count} nulos")
    else:
        print("  ✅ Sin valores nulos")

    # Validación de rangos
    if (df['IngresoTotal'] < 0).any():
        print("  ⚠️ Existen registros con IngresoTotal negativo")
    else:
        print("  ✅ IngresoTotal sin valores negativos")

    if (df['Cantidad'] <= 0).any():
        print("  ⚠️ Existen registros con Cantidad <= 0")
    else:
        print("  ✅ Cantidad siempre positiva")


# ── EJECUCIÓN PRINCIPAL ────────────────────────────────────────────────────────

if __name__ == "__main__":
    inicio = datetime.now()
    print("🚀 Iniciando transformación de datos...\n")

    print("📥 Extrayendo datos desde SQL Server...")
    df_ventas, df_clientes, df_productos, df_vendedores, df_tiempo = extract_tables()
    print("  ✅ Extracción completada\n")

    print("🔄 Transformando datos...")
    df_final = build_analytical_dataset(
        df_ventas, df_clientes, df_productos, df_vendedores, df_tiempo
    )
    df_final = add_calculated_columns(df_final)
    print("  ✅ Transformación completada")

    validate_data(df_final)

    # Guarda el dataset consolidado
    os.makedirs(DATA_PROCESSED, exist_ok=True)
    output_path = f"{DATA_PROCESSED}/ventas_consolidado.csv"
    df_final.to_csv(output_path, index=False)

    fin = datetime.now()
    duracion = (fin - inicio).seconds

    print(f"\n💾 Dataset guardado en: {output_path}")
    print(f"   Dimensiones: {df_final.shape[0]:,} filas x {df_final.shape[1]} columnas")
    print(f"\n🎉 Transformación completada en {duracion} segundos")
