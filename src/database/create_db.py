# src/database/create_db.py
import pyodbc
import sys
import os

# Agregamos el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.config import DB_SERVER, DB_NAME

def create_database():
    """
    Crea la base de datos SalesIntelligenceDB en SQL Server
    si no existe todavía.
    """
    try:
        # Conexión al servidor sin especificar base de datos
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={DB_SERVER};"
            f"DATABASE=master;"
            f"Trusted_Connection=yes;"
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Verifica si la base de datos ya existe
        cursor.execute(f"""
            IF NOT EXISTS (
                SELECT name FROM sys.databases WHERE name = '{DB_NAME}'
            )
            BEGIN
                CREATE DATABASE [{DB_NAME}]
                PRINT 'Base de datos {DB_NAME} creada exitosamente.'
            END
            ELSE
                PRINT 'La base de datos {DB_NAME} ya existe.'
        """)

        print(f"✅ Base de datos '{DB_NAME}' lista en {DB_SERVER}")
        cursor.close()
        conn.close()

    except pyodbc.Error as e:
        print(f"❌ Error al crear la base de datos: {e}")
        sys.exit(1)


def create_tables():
    """
    Crea todas las tablas del modelo dimensional:
    - DimClientes
    - DimProductos
    - DimVendedores
    - DimTiempo
    - FactVentas
    """
    try:
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={DB_SERVER};"
            f"DATABASE={DB_NAME};"
            f"Trusted_Connection=yes;"
        )
        cursor = conn.cursor()

        # ── DIMENSIÓN CLIENTES ──────────────────────────────────────────
        cursor.execute("""
            IF NOT EXISTS (
                SELECT * FROM sysobjects WHERE name='DimClientes' AND xtype='U'
            )
            CREATE TABLE DimClientes (
                ClienteID     INT PRIMARY KEY,
                Nombre        VARCHAR(100) NOT NULL,
                Email         VARCHAR(100),
                Telefono      VARCHAR(20),
                Ciudad        VARCHAR(50),
                Region        VARCHAR(50),
                Segmento      VARCHAR(30),
                FechaRegistro DATE
            )
        """)
        print("✅ Tabla DimClientes lista")

        # ── DIMENSIÓN PRODUCTOS ─────────────────────────────────────────
        cursor.execute("""
            IF NOT EXISTS (
                SELECT * FROM sysobjects WHERE name='DimProductos' AND xtype='U'
            )
            CREATE TABLE DimProductos (
                ProductoID    INT PRIMARY KEY,
                Nombre        VARCHAR(100) NOT NULL,
                Categoria     VARCHAR(50),
                SubCategoria  VARCHAR(50),
                Marca         VARCHAR(50),
                CostoUnitario DECIMAL(10,2),
                PrecioVenta   DECIMAL(10,2)
            )
        """)
        print("✅ Tabla DimProductos lista")

        # ── DIMENSIÓN VENDEDORES ────────────────────────────────────────
        cursor.execute("""
            IF NOT EXISTS (
                SELECT * FROM sysobjects WHERE name='DimVendedores' AND xtype='U'
            )
            CREATE TABLE DimVendedores (
                VendedorID    INT PRIMARY KEY,
                Nombre        VARCHAR(100) NOT NULL,
                Email         VARCHAR(100),
                Region        VARCHAR(50),
                Zona          VARCHAR(50),
                FechaIngreso  DATE
            )
        """)
        print("✅ Tabla DimVendedores lista")

        # ── DIMENSIÓN TIEMPO ────────────────────────────────────────────
        cursor.execute("""
            IF NOT EXISTS (
                SELECT * FROM sysobjects WHERE name='DimTiempo' AND xtype='U'
            )
            CREATE TABLE DimTiempo (
                TiempoID      INT PRIMARY KEY,
                Fecha         DATE NOT NULL,
                Anio          INT,
                Trimestre     INT,
                Mes           INT,
                NombreMes     VARCHAR(20),
                Semana        INT,
                DiaSemana     VARCHAR(20),
                EsFinDeSemana BIT
            )
        """)
        print("✅ Tabla DimTiempo lista")

        # ── TABLA DE HECHOS VENTAS ──────────────────────────────────────
        cursor.execute("""
            IF NOT EXISTS (
                SELECT * FROM sysobjects WHERE name='FactVentas' AND xtype='U'
            )
            CREATE TABLE FactVentas (
                VentaID       INT PRIMARY KEY,
                TiempoID      INT FOREIGN KEY REFERENCES DimTiempo(TiempoID),
                ClienteID     INT FOREIGN KEY REFERENCES DimClientes(ClienteID),
                ProductoID    INT FOREIGN KEY REFERENCES DimProductos(ProductoID),
                VendedorID    INT FOREIGN KEY REFERENCES DimVendedores(VendedorID),
                Cantidad      INT,
                PrecioUnitario DECIMAL(10,2),
                Descuento     DECIMAL(5,2),
                CostoTotal    DECIMAL(10,2),
                IngresoTotal  DECIMAL(10,2),
                Ganancia      DECIMAL(10,2)
            )
        """)
        print("✅ Tabla FactVentas lista")

        conn.commit()
        cursor.close()
        conn.close()
        print("\n🎉 Modelo dimensional creado exitosamente")

    except pyodbc.Error as e:
        print(f"❌ Error al crear las tablas: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("🚀 Iniciando creación de base de datos...\n")
    create_database()
    print("\n🚀 Creando modelo dimensional...\n")
    create_tables()