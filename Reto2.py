# -*- coding: utf-8 -*-
"""
Created on Wed Oct 15 11:06:55 2025

@author: USER 40725
"""

import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import date
import altair as alt

DB_FILE = "contabilidad.db"

ANALYSIS_TABLES = [
    "caja2025", "caja2024", "caja2023", "caja2022", "caja2020", 
    "edr2025", "edr2024", "bancos2022" 
] 
SOCIOS_TABLES = [
    "socios2024", "socios2023", "socios2022", "socios2020"
]

def init_db_connection():
    """Establece la conexión a la base de datos SQLite."""
    try:
        conn = sqlite3.connect(DB_FILE, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        return conn
    except sqlite3.Error as e:
        st.error(f"Error al conectar a la base de datos: {e}")
        return None

def run_query(conn, query):
    """Ejecuta una consulta SQL y retorna los resultados como DataFrame."""
    try:
        df = pd.read_sql_query(query, conn)
        return df
    except pd.io.sql.DatabaseError as e:
        st.error(f"Error al ejecutar la consulta: {e}")
        return pd.DataFrame()

def get_socios_list(conn, socios_table):
    """Obtiene la lista de socios de la tabla seleccionada."""
    query = f"PRAGMA table_info({socios_table})"
    info_df = run_query(conn, query)
    
    name_col = 'nombre'
    if 'socio' in info_df['name'].tolist():
        name_col = 'socio'
    
    socios_query = f"SELECT {name_col} FROM \"{socios_table}\" WHERE {name_col} IS NOT NULL"
    try:
        socios_df = pd.read_sql_query(socios_query, conn)
        return ["Todos"] + socios_df[name_col].str.strip().tolist()
    except Exception:
        return ["Todos"]

# ----------------------------------------------------------------------
# FUNCIÓN: Análisis Mensual
# ----------------------------------------------------------------------
def render_monthly_analysis(conn):
    st.header("📊 Caja mensual")
    st.markdown("Calcula los totales de entradas y salidas por mes dentro de un rango de fechas.")

    # Widgets en el sidebar
    st.sidebar.subheader("Filtros para Análisis Mensual")
    selected_table = st.sidebar.selectbox("Tabla para Análisis Mensual:", ANALYSIS_TABLES, key="monthly_table", index=ANALYSIS_TABLES.index("edr2025") if "edr2025" in ANALYSIS_TABLES else 0)
    default_start = date(date.today().year, 1, 1)
    default_end = date.today()
    date_start = st.sidebar.date_input("Fecha de inicio (Mensual)", value=default_start, key="monthly_start", min_value=date(2020, 1, 1))
    date_end = st.sidebar.date_input("Fecha de fin (Mensual)", value=default_end, key="monthly_end", min_value=date_start)
    st.sidebar.markdown("---")
    
    start_date_str = date_start.strftime('%Y-%m-%d')
    end_date_str = date_end.strftime('%Y-%m-%d')

    sql_query = f"""
    SELECT 
        strftime('%Y-%m', fecha) as Mes_Anio,
        SUM(entrada) as Total_Entrada,
        SUM(salida) as Total_Salida,
        SUM(entrada) - SUM(salida) as Flujo_Neto
    FROM 
        "{selected_table}"
    WHERE 
        fecha BETWEEN '{start_date_str}' AND '{end_date_str}'
    GROUP BY 
        Mes_Anio
    ORDER BY 
        Mes_Anio;
    """

    st.info(f"Rango de Fechas: *{start_date_str}* hasta *{end_date_str}*")

    df_results = run_query(conn, sql_query)

    if not df_results.empty:
        df_results['Fecha_Grafico'] = pd.to_datetime(df_results['Mes_Anio'])

        # --- Gráfico de Flujo Neto Mensual ---
        st.subheader("📉 Flujo Neto Mensual")
        flujo_neto_chart = alt.Chart(df_results).mark_bar().encode(
            x=alt.X('Fecha_Grafico', title='Mes', axis=alt.Axis(format='%b %Y')),
            y=alt.Y('Flujo_Neto', title='Flujo Neto (USD)'),
            color=alt.condition(alt.datum.Flujo_Neto > 0, alt.value('#2ca02c'), alt.value('#d62728')),
            tooltip=['Mes_Anio', alt.Tooltip('Flujo_Neto', format=',.0f')]
        ).properties(title="Ganancia/Pérdida Neta por Mes").interactive()
        st.altair_chart(flujo_neto_chart, use_container_width=True)

        st.subheader("Tabla de Totales Mensuales")
        st.dataframe(df_results[['Mes_Anio', 'Total_Entrada', 'Total_Salida', 'Flujo_Neto']].set_index('Mes_Anio').style.format(precision=0), use_container_width=True)
        
        # Resumen total
        total_entrada_periodo = df_results['Total_Entrada'].sum()
        total_salida_periodo = df_results['Total_Salida'].sum()
        flujo_neto_periodo = total_entrada_periodo - total_salida_periodo

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Entradas", f"${total_entrada_periodo:,.0f}", "✔️")
        col2.metric("Total Salidas", f"${total_salida_periodo:,.0f}", "🔴")
        col3.metric("Flujo Neto", f"${flujo_neto_periodo:,.0f}", "⚖")

        # --- CONCLUSIÓN ---
        max_flujo_neto = df_results['Flujo_Neto'].max()
        mes_max_flujo = df_results.loc[df_results['Flujo_Neto'].idxmax(), 'Mes_Anio']
        
        st.markdown("---")
        st.subheader("Conclusión del Análisis Mensual")
        st.success(f"💰 *El mejor mes* fue *{mes_max_flujo}* con un Flujo Neto de ${max_flujo_neto:,.0f}. El propósito de esta consulta es *poder identificar satisfactoriamente los períodos más rentables y monitorear la tendencia de caja*.")


    else:
        st.warning(f"No se encontraron datos para la tabla '{selected_table}' en el rango de fechas seleccionado.")

# ----------------------------------------------------------------------
# FUNCIÓN: Top 10 Gastos
# ----------------------------------------------------------------------
def render_top_expenses(conn):
    st.header("💸 Top 10 egresos (Caja)")
    st.markdown("Identifica los detalles que representan el mayor egreso en un rango de fechas.")
    
    with st.form("top_expenses_form"):
        col1, col2, col3 = st.columns(3)
        
        selected_table = col1.selectbox("Tabla para Análisis de Gasto:", ANALYSIS_TABLES, key="expense_table", index=ANALYSIS_TABLES.index("edr2025") if "edr2025" in ANALYSIS_TABLES else 0)
        default_start = date(date.today().year, 1, 1)
        default_end = date.today()
        date_start = col2.date_input("Fecha de inicio (Gasto)", value=default_start, key="expense_start", min_value=date(2020, 1, 1))
        date_end = col3.date_input("Fecha de fin (Gasto)", value=default_end, key="expense_end", min_value=date_start)
        
        submitted = st.form_submit_button("Consultar Top 10 Gastos")

    if submitted:
        start_date_str = date_start.strftime('%Y-%m-%d')
        end_date_str = date_end.strftime('%Y-%m-%d')
        
        st.info(f"Analizando gastos (columna *salida) de **{selected_table}* entre *{start_date_str}* y *{end_date_str}*.")

        sql_query = f"""
        SELECT 
            detalle,
            SUM(salida) as Gasto_Total
        FROM 
            "{selected_table}"
        WHERE 
            fecha BETWEEN '{start_date_str}' AND '{end_date_str}'
            AND salida > 0
            AND detalle IS NOT NULL 
        GROUP BY 
            detalle
        ORDER BY 
            Gasto_Total DESC
        LIMIT 10;
        """

        df_top_expenses = run_query(conn, sql_query)

        if not df_top_expenses.empty:
            st.subheader("Top 10 Detalles de Mayor Gasto")
            
            chart = alt.Chart(df_top_expenses).mark_bar().encode(
                y=alt.Y('detalle', title='Detalle del Gasto', sort='-x'),
                x=alt.X('Gasto_Total', title='Gasto Total (USD)'),
                color=alt.value('#ff4b4b'),
                tooltip=['detalle', alt.Tooltip('Gasto_Total', format=',.0f')]
            ).properties(title=f"Top 10 Gastos en '{selected_table}'").interactive()
            
            st.altair_chart(chart, use_container_width=True)
            
            st.dataframe(df_top_expenses.style.format({'Gasto_Total': '${:,.0f}'}), use_container_width=True)

            # --- CONCLUSIÓN ---
            top_detalle = df_top_expenses.iloc[0]['detalle']
            top_monto = df_top_expenses.iloc[0]['Gasto_Total']
            
            st.markdown("---")
            st.subheader("Conclusión del Top 10 Gastos")
            st.error(f"⚠ El *mayor gasto* es *{top_detalle}* con ${top_monto:,.0f}. El propósito de esta consulta es **enfocar la revisión y optimización de costos en los conceptos de mayor impacto*.")

        else:
            st.warning("No se encontraron gastos (salidas) para los filtros seleccionados.")
            
    elif not submitted:
        st.info("Presiona 'Consultar Top 10 Gastos' para ver los resultados.")


# ----------------------------------------------------------------------
# FUNCIÓN: Concentración de Ingresos
# ----------------------------------------------------------------------
def render_socio_income(conn):
    st.header("📈 Concentración de Ingresos por Socio (CXC)")
    st.markdown("Muestra la distribución de ingresos por socio en un período de tiempo.")

    with st.form("socio_income_form"):
        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)

        income_table = col1.selectbox("Tabla Contable (Ingresos):", ANALYSIS_TABLES, key="income_table", index=ANALYSIS_TABLES.index("edr2025") if "edr2025" in ANALYSIS_TABLES else 0)
        socios_table = col2.selectbox("Tabla de Socios (referencia):", SOCIOS_TABLES, key="socios_table", index=0)
        
        socios_list = get_socios_list(conn, socios_table)
        selected_socio = col3.selectbox("Socio a Analizar:", socios_list, key="selected_socio")

        default_start = date(date.today().year, 1, 1)
        default_end = date.today()
        date_range = col4.date_input("Rango de Fechas:", value=[default_start, default_end], key="income_date_range", min_value=date(2020, 1, 1))
        
        submitted = st.form_submit_button("Consultar Ingresos")

    if submitted and len(date_range) == 2:
        start_date_str = date_range[0].strftime('%Y-%m-%d')
        end_date_str = date_range[1].strftime('%Y-%m-%d')
        
        st.info(f"Analizando ingresos de *{income_table}* entre *{start_date_str}* y *{end_date_str}*.")

        socio_filter = ""
        if selected_socio != "Todos":
            socio_filter = f"AND detalle LIKE '%{selected_socio.strip()}%'" 

        sql_query = f"""
        SELECT 
            fecha,
            detalle,
            entrada as Ingreso
        FROM 
            "{income_table}"
        WHERE 
            fecha BETWEEN '{start_date_str}' AND '{end_date_str}'
            AND entrada > 0
            {socio_filter}
        ORDER BY
            fecha;
        """

        df_income = run_query(conn, sql_query)
        df_income['fecha'] = pd.to_datetime(df_income['fecha'])

        if not df_income.empty:
            
            if selected_socio == "Todos":
                # --- VISUALIZACIÓN A: Barras para TODOS los Socios ---
                st.subheader("Concentración de Ingresos por Socio/Detalle")
                df_grouped = df_income.groupby('detalle')['Ingreso'].sum().reset_index(name='Ingreso_Total')
                
                chart = alt.Chart(df_grouped).mark_bar().encode(
                    y=alt.Y('detalle', title='Detalle / Socio', sort='-x'),
                    x=alt.X('Ingreso_Total', title='Ingreso Total (USD)'),
                    color=alt.value('#1E90FF'),
                    tooltip=['detalle', alt.Tooltip('Ingreso_Total', format=',.0f')]
                ).properties(title=f"Ingresos Totales Agrupados por Detalle ({start_date_str} a {end_date_str})").interactive()
                
                st.altair_chart(chart, use_container_width=True)
                
                # --- CONCLUSIÓN (Todos) ---
                max_socio = df_grouped.loc[df_grouped['Ingreso_Total'].idxmax(), 'detalle']
                max_ingreso = df_grouped['Ingreso_Total'].max()
                st.markdown("---")
                st.subheader("Conclusión de Concentración de Ingresos")
                st.info(f"👑 *El mayor contribuidor* de ingresos es *{max_socio}* con un total de ${max_ingreso:,.0f}. El propósito de esta consulta es *medir la dependencia del ingreso en socios/conceptos clave* y evaluar la diversificación.")

            else:
                # --- VISUALIZACIÓN B: Línea temporal para UN Socio ---
                st.subheader(f"Evolución Temporal de Ingresos: {selected_socio}")
                
                chart = alt.Chart(df_income).mark_line(point=True).encode(
                    x=alt.X('fecha', title='Fecha', axis=alt.Axis(format='%Y-%m-%d')),
                    y=alt.Y('Ingreso', title='Monto de Ingreso (USD)'),
                    color=alt.value('#FFD700'),
                    tooltip=['fecha', 'detalle', alt.Tooltip('Ingreso', format=',.0f')]
                ).properties(title=f"Ingresos de {selected_socio} en el tiempo").interactive()
                
                st.altair_chart(chart, use_container_width=True)

                # --- CONCLUSIÓN (Individual) ---
                total_socio = df_income['Ingreso'].sum()
                num_transacciones = df_income.shape[0]
                st.markdown("---")
                st.subheader("Conclusión de Concentración de Ingresos")
                st.info(f"👤 El socio *{selected_socio}* generó un total de *${total_socio:,.0f}* en *{num_transacciones} transacciones. El propósito de esta consulta es **analizar la estabilidad y frecuencia del flujo de ingreso individual*.")

        else:
            st.warning(f"No se encontraron ingresos para el socio/detalle '{selected_socio}' en el rango de fechas seleccionado.")

    elif not submitted:
        st.info("Selecciona las opciones y haz clic en 'Consultar Ingresos' para ver el análisis.")


# ----------------------------------------------------------------------
# FUNCIÓN: Principal
# ----------------------------------------------------------------------
def main():
    st.set_page_config(page_title="Gestor Contable Avanzado", layout="wide")
    st.title("Sistema de Análisis Contable 🏦")
    
    if not os.path.exists(DB_FILE):
        st.error(f"¡Error! El archivo de base de datos '{DB_FILE}' no se encontró.")
        return

    conn = init_db_connection()

    if conn is not None:
        
        tab1, tab2, tab3 = st.tabs(["📊 Análisis Mensual", "💸 Top 10 Gastos", "💰 Concentración de Ingresos"])

        with tab1:
            render_monthly_analysis(conn)

        with tab2:
            render_top_expenses(conn)

        with tab3:
            render_socio_income(conn)

        conn.close()

if __name__ == "__main__":
    main()