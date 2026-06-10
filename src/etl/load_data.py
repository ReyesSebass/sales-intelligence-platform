# src/etl/load_data.py
import pandas as pd
import pyodbc
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.config import DB_SERVER, DB_NAME, DATA_RAW

# ── CONEXIÓN ─────────────────────────────────────────────────────────────────

def get_connection():
    """Retorna una conexión activa a SQL Server."""
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"Trusted_Connection=yes;"
    )


# ── CARGA DE TABLAS ───────────────────────────────────────────────────────────

def load_table(df, table_name, insert_sql, transform_fn=None):
    """
    Función genérica para cargar cualquier DataFrame a SQL Server.
    Usa executemany para inserción eficiente en lotes.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    # Limpia la tabla antes de insertar
    cursor.execute(f"DELETE FROM {table_name}")
    print(f"  → Tabla {table_name} limpiada")

    # Aplica transformación si existe
    rows = transform_fn(df) if transform_fn else df.values.tolist()

    # Inserta en lotes de 1000 registros
    batch_size = 1000
    total      = len(rows)

    for i in range(0, total, batch_size):
        batch = rows[i:i + batch_size]
        cursor.executemany(insert_sql, batch)

        if (i + batch_size) % 10000 == 0 or (i + batch_size) >= total:
            print(f"    → {min(i + batch_size, total):,} / {total:,} registros insertados...")

    conn.commit()
    cursor.close()
    conn.close()
    print(f"  ✅ {table_name} cargada exitosamente ({total:,} registros)\n")


def load_clientes():
    print("📦 Cargando DimClientes...")
    df = pd.read_csv(f"{DATA_RAW}/clientes.csv")

    sql = """
        INSERT INTO DimClientes 
        (ClienteID, Nombre, Email, Telefono, Ciudad, Region, Segmento, FechaRegistro)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """

    def transform(df):
        return df[[
            'ClienteID', 'Nombre', 'Email', 'Telefono',
            'Ciudad', 'Region', 'Segmento', 'FechaRegistro'
        ]].values.tolist()

    load_table(df, "DimClientes", sql, transform)


def load_productos():
    print("📦 Cargando DimProductos...")
    df = pd.read_csv(f"{DATA_RAW}/productos.csv")

    sql = """
        INSERT INTO DimProductos
        (ProductoID, Nombre, Categoria, SubCategoria, Marca, CostoUnitario, PrecioVenta)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """

    def transform(df):
        return df[[
            'ProductoID', 'Nombre', 'Categoria', 'SubCategoria',
            'Marca', 'CostoUnitario', 'PrecioVenta'
        ]].values.tolist()

    load_table(df, "DimProductos", sql, transform)


def load_vendedores():
    print("📦 Cargando DimVendedores...")
    df = pd.read_csv(f"{DATA_RAW}/vendedores.csv")

    sql = """
        INSERT INTO DimVendedores
        (VendedorID, Nombre, Email, Region, Zona, FechaIngreso)
        VALUES (?, ?, ?, ?, ?, ?)
    """

    def transform(df):
        return df[[
            'VendedorID', 'Nombre', 'Email',
            'Region', 'Zona', 'FechaIngreso'
        ]].values.tolist()

    load_table(df, "DimVendedores", sql, transform)


def load_tiempo():
    print("📦 Cargando DimTiempo...")
    df = pd.read_csv(f"{DATA_RAW}/tiempo.csv")

    sql = """
        INSERT INTO DimTiempo
        (TiempoID, Fecha, Anio, Trimestre, Mes, NombreMes, Semana, DiaSemana, EsFinDeSemana)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    def transform(df):
        rows = []
        for _, row in df.iterrows():
            rows.append([
                int(row['TiempoID']),
                row['Fecha'],
                int(row['Anio']),
                int(row['Trimestre']),
                int(row['Mes']),
                row['NombreMes'],
                int(row['Semana']),
                row['DiaSemana'],
                bool(row['EsFinDeSemana']),
            ])
        return rows

    load_table(df, "DimTiempo", sql, transform)


def load_ventas():
    print("📦 Cargando FactVentas...")
    df = pd.read_csv(f"{DATA_RAW}/ventas.csv")

    sql = """
        INSERT INTO FactVentas
        (VentaID, TiempoID, ClienteID, ProductoID, VendedorID,
         Cantidad, PrecioUnitario, Descuento, CostoTotal, IngresoTotal, Ganancia)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    def transform(df):
        return df[[
            'VentaID', 'TiempoID', 'ClienteID', 'ProductoID', 'VendedorID',
            'Cantidad', 'PrecioUnitario', 'Descuento',
            'CostoTotal', 'IngresoTotal', 'Ganancia'
        ]].values.tolist()

    load_table(df, "FactVentas", sql, transform)


# ── EJECUCIÓN PRINCIPAL ───────────────────────────────────────────────────────

if __name__ == "__main__":
    inicio = datetime.now()
    print("🚀 Iniciando carga de datos a SQL Server...\n")
    print(f"  Servidor : {DB_SERVER}")
    print(f"  Base de datos : {DB_NAME}\n")

    try:
        # El orden importa por las Foreign Keys
        load_clientes()
        load_productos()
        load_vendedores()
        load_tiempo()
        load_ventas()

        fin      = datetime.now()
        duracion = (fin - inicio).seconds

        print("=" * 50)
        print(f"🎉 Carga completada en {duracion} segundos")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ Error durante la carga: {e}")
        sys.exit(1)