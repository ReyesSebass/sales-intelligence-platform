# src/analysis/kpis.py
import pandas as pd
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.config import DATA_PROCESSED


# ── CARGA DE DATOS ───────────────────────────────────────────────────────────

def load_dataset():
    """Carga el dataset consolidado y asegura tipos correctos."""
    path = f"{DATA_PROCESSED}/ventas_consolidado.csv"
    df = pd.read_csv(path)
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    return df


# ── KPIs GENERALES ───────────────────────────────────────────────────────────

def kpis_generales(df):
    """KPIs globales del negocio."""
    return {
        'VentasTotales':       round(df['IngresoTotal'].sum(), 2),
        'GananciaTotal':       round(df['Ganancia'].sum(), 2),
        'CostoTotal':          round(df['CostoTotal'].sum(), 2),
        'MargenPromedio':      round(df['MargenPorcentaje'].mean(), 2),
        'TicketPromedio':      round(df['IngresoTotal'].mean(), 2),
        'UnidadesVendidas':    int(df['Cantidad'].sum()),
        'TotalTransacciones':  len(df),
        'ClientesUnicos':      df['ClienteID'].nunique(),
        'ProductosVendidos':   df['ProductoID'].nunique(),
    }


# ── TENDENCIAS TEMPORALES ────────────────────────────────────────────────────

def ventas_por_mes(df):
    """Ventas, ganancia y unidades agrupadas por Año-Mes."""
    return (
        df.groupby('AnioMes')
          .agg(
              VentasTotales=('IngresoTotal', 'sum'),
              GananciaTotal=('Ganancia', 'sum'),
              Unidades=('Cantidad', 'sum'),
              Transacciones=('VentaID', 'count')
          )
          .reset_index()
          .sort_values('AnioMes')
    )


def comparativa_anual(df):
    """Comparativa de ventas y ganancia entre 2023 y 2024."""
    return (
        df.groupby('Anio')
          .agg(
              VentasTotales=('IngresoTotal', 'sum'),
              GananciaTotal=('Ganancia', 'sum'),
              Unidades=('Cantidad', 'sum'),
              Transacciones=('VentaID', 'count')
          )
          .reset_index()
    )


# ── TOP RANKINGS ─────────────────────────────────────────────────────────────

def top_productos(df, n=10):
    """Top N productos por ingreso total."""
    return (
        df.groupby(['ProductoID', 'NombreProducto', 'Categoria'])
          .agg(
              VentasTotales=('IngresoTotal', 'sum'),
              GananciaTotal=('Ganancia', 'sum'),
              Unidades=('Cantidad', 'sum')
          )
          .reset_index()
          .sort_values('VentasTotales', ascending=False)
          .head(n)
    )


def top_vendedores(df, n=10):
    """Top N vendedores por ingreso generado."""
    return (
        df.groupby(['VendedorID', 'NombreVendedor', 'RegionVendedor'])
          .agg(
              VentasTotales=('IngresoTotal', 'sum'),
              GananciaTotal=('Ganancia', 'sum'),
              Transacciones=('VentaID', 'count')
          )
          .reset_index()
          .sort_values('VentasTotales', ascending=False)
          .head(n)
    )


def top_clientes(df, n=10):
    """Top N clientes por gasto total."""
    return (
        df.groupby(['ClienteID', 'NombreCliente', 'SegmentoCliente'])
          .agg(
              VentasTotales=('IngresoTotal', 'sum'),
              Transacciones=('VentaID', 'count')
          )
          .reset_index()
          .sort_values('VentasTotales', ascending=False)
          .head(n)
    )


# ── ANÁLISIS POR DIMENSIÓN ───────────────────────────────────────────────────

def ventas_por_region(df):
    """Ventas agrupadas por región del cliente."""
    return (
        df.groupby('RegionCliente')
          .agg(
              VentasTotales=('IngresoTotal', 'sum'),
              GananciaTotal=('Ganancia', 'sum'),
              Transacciones=('VentaID', 'count')
          )
          .reset_index()
          .sort_values('VentasTotales', ascending=False)
    )


def ventas_por_categoria(df):
    """Ventas agrupadas por categoría de producto."""
    return (
        df.groupby('Categoria')
          .agg(
              VentasTotales=('IngresoTotal', 'sum'),
              GananciaTotal=('Ganancia', 'sum'),
              MargenPromedio=('MargenPorcentaje', 'mean'),
              Unidades=('Cantidad', 'sum')
          )
          .reset_index()
          .sort_values('VentasTotales', ascending=False)
    )


def ventas_por_segmento(df):
    """Ventas agrupadas por segmento de cliente."""
    return (
        df.groupby('SegmentoCliente')
          .agg(
              VentasTotales=('IngresoTotal', 'sum'),
              GananciaTotal=('Ganancia', 'sum'),
              Transacciones=('VentaID', 'count'),
              DescuentoPromedio=('Descuento', 'mean')
          )
          .reset_index()
          .sort_values('VentasTotales', ascending=False)
    )


# ── EJECUCIÓN PRINCIPAL ───────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🚀 Calculando KPIs de negocio...\n")

    df = load_dataset()

    print("📊 KPIs Generales")
    print("-" * 50)
    generales = kpis_generales(df)
    for k, v in generales.items():
        print(f"  {k:25}: {v:,}")

    print("\n📈 Comparativa Anual")
    print("-" * 50)
    print(comparativa_anual(df).to_string(index=False))

    print("\n🏆 Top 5 Productos")
    print("-" * 50)
    print(top_productos(df, 5).to_string(index=False))

    print("\n🏆 Top 5 Vendedores")
    print("-" * 50)
    print(top_vendedores(df, 5).to_string(index=False))

    print("\n🏆 Top 5 Clientes")
    print("-" * 50)
    print(top_clientes(df, 5).to_string(index=False))

    print("\n🌎 Ventas por Región")
    print("-" * 50)
    print(ventas_por_region(df).to_string(index=False))

    print("\n📦 Ventas por Categoría")
    print("-" * 50)
    print(ventas_por_categoria(df).to_string(index=False))

    print("\n👥 Ventas por Segmento")
    print("-" * 50)
    print(ventas_por_segmento(df).to_string(index=False))

    print("\n🎉 Cálculo de KPIs completado")