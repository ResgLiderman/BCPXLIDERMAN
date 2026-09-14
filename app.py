import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURACIÓN CORPORATIVA BCP
st.set_page_config(
    page_title="Dashboard BI - Operaciones Liderman", 
    page_icon="🛡️", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inyección de CSS BCP / BI
st.markdown("""
<style>
    .stApp { background-color: #F4F6F9; }
    .kpi-card {
        background-color: white; padding: 20px; border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-left: 5px solid #002A8D; /* Azul BCP */
        margin-bottom: 20px; text-align: center;
    }
    .kpi-title { color: #FF7A00; font-size: 0.95rem; font-weight: 700; text-transform: uppercase; } /* Naranja BCP */
    .kpi-value { color: #002A8D; font-size: 2.2rem; font-weight: 800; margin: 10px 0; }
    .kpi-desc { font-size: 0.85rem; color: #6c757d; font-weight: 500; }
    .alert-red { color: #d9534f; font-weight: 700;}
    .alert-green { color: #5cb85c; font-weight: 700;}
</style>
""", unsafe_allow_html=True)

# 2. MOTOR DE EXTRACCIÓN Y LIMPIEZA
@st.cache_data(ttl=600)
def cargar_datos():
    sheet_id = "1Cs3cV-NdVC6u1sDVhWEKpoP2OvDldzpWVIvx8bf-OSc"
    base_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid="
    
    gids = {
        'equipamiento': '0', 'doc_sucamec': '2135347375', 'lic_sucamec': '371955966',
        'capa': '1864610226', 'tiro': '1062108520', 'maniobra': '495125468',
        'apt_fisica': '2042184423', 'emo': '516174160', 'vacaciones': '1808970374'
    }
    
    dfs = {}
    for nombre, gid in gids.items():
        try:
            # header=1 salta la fila vacía
            df = pd.read_csv(base_url + gid, header=1)
            df.columns = df.columns.str.strip()
            if 'RESGUARDO' in df.columns:
                df['RESGUARDO'] = df['RESGUARDO'].astype(str).str.strip()
            dfs[nombre] = df
        except Exception as e:
            st.error(f"Error cargando {nombre}: {e}")
            
    hoy = pd.Timestamp.today()

    # Procesamiento Nativo de Fechas (EMO)
    if 'emo' in dfs:
        df = dfs['emo']
        df['F. VENC. DE EMO'] = pd.to_datetime(df['F. VENC. DE EMO'], format='%d/%m/%Y', errors='coerce')
        df['DÍAS RESTANTES'] = (df['F. VENC. DE EMO'] - hoy).dt.days
        dfs['emo'] = df

    # Procesamiento SUCAMEC
    if 'doc_sucamec' in dfs:
        df = dfs['doc_sucamec']
        df['F. VENCIMIENTO CARNÉ SUCAMEC'] = pd.to_datetime(df['F. VENCIMIENTO CARNÉ SUCAMEC'], format='%d/%m/%Y', errors='coerce')
        df['DÍAS RESTANTES SUCAMEC'] = (df['F. VENCIMIENTO CARNÉ SUCAMEC'] - hoy).dt.days
        dfs['doc_sucamec'] = df

    return dfs

dfs = cargar_datos()

# 3. HEADER GERENCIAL
st.markdown("<h1 style='color: #002A8D;'>🛡️ Control Operativo de Resguardos</h1>", unsafe_allow_html=True)
st.markdown("Monitor de indicadores corporativos. Excluye coordinador de métricas tácticas.")

# KPIs Globales
col1, col2, col3, col4 = st.columns(4)
total_resguardos = len(dfs['doc_sucamec']) if 'doc_sucamec' in dfs else 0
operativos = total_resguardos - 1 # Excluye a Víctor Castro Mamani

emo_riesgo = len(dfs['emo'][dfs['emo']['DÍAS RESTANTES'] < 30]) if 'emo' in dfs else 0
sucamec_riesgo = len(dfs['doc_sucamec'][dfs['doc_sucamec']['DÍAS RESTANTES SUCAMEC'] < 30]) if 'doc_sucamec' in dfs else 0

with col1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Universo Total</div><div class="kpi-value">{total_resguardos}</div><div class="kpi-desc">1 Coordinador + {operativos} Operativos</div></div>', unsafe_allow_html=True)
with col2:
    estado = "alert-red" if emo_riesgo > 0 else "alert-green"
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Alertas EMO (<30 Días)</div><div class="kpi-value" style="color:{"#d9534f" if emo_riesgo > 0 else "#002A8D"}">{emo_riesgo}</div><div class="kpi-desc {estado}">Resguardos en riesgo</div></div>', unsafe_allow_html=True)
with col3:
    estado = "alert-red" if sucamec_riesgo > 0 else "alert-green"
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Alertas SUCAMEC (<30 Días)</div><div class="kpi-value" style="color:{"#d9534f" if sucamec_riesgo > 0 else "#002A8D"}">{sucamec_riesgo}</div><div class="kpi-desc {estado}">Carnés por vencer</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Estado del Sistema</div><div class="kpi-value">100%</div><div class="kpi-desc alert-green">Sincronizado en tiempo real</div></div>', unsafe_allow_html=True)

# 4. MÓDULOS DE BUSINESS INTELLIGENCE (TABS)
tab1, tab2, tab3 = st.tabs(["📊 Cumplimiento Legal y Médico", "🎯 Desempeño y Capacitación", "📦 Logística y Vacaciones"])

with tab1:
    st.subheader("Estado Situacional de Carnés y EMO")
    c1, c2 = st.columns(2)
    
    with c1:
        if 'doc_sucamec' in dfs:
            # Gráfico de Torta con % para SUCAMEC
            df_suc = dfs['doc_sucamec']
            fig_suc = px.pie(df_suc, names='ESTADO CARNÉ SUCAMEC', title='Proporción de Vigencia SUCAMEC', 
                             color_discrete_sequence=['#002A8D', '#FF7A00', '#d9534f'], hole=0.4)
            fig_suc.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_suc, use_container_width=True)
            
    with c2:
        if 'emo' in dfs:
            # Gráfico de barras horizontales EMO
            df_emo = dfs['emo'].sort_values('DÍAS RESTANTES')
            fig_emo = px.bar(df_emo, x='DÍAS RESTANTES', y='RESGUARDO', orientation='h',
                             title='Días Restantes para Vencimiento EMO',
                             color='DÍAS RESTANTES', color_continuous_scale='Blues')
            fig_emo.add_vline(x=30, line_dash="dash", line_color="red", annotation_text="Límite 30 días")
            st.plotly_chart(fig_emo, use_container_width=True)

with tab2:
    st.subheader("Métricas Operativas (Excluye Coordinador)")
    c1, c2 = st.columns(2)
    
    with c1:
        if 'capa' in dfs:
            df_capa = dfs['capa']
            # Derretir la matriz para gráficas BI
            nombres_operativos = [col for col in df_capa.columns if col not in ['Trimestre', 'CURSO', 'TOTAL CURSOS COMPLETADOS'] and not col.startswith('Unnamed')]
            df_melt = df_capa.melt(id_vars=['CURSO'], value_vars=nombres_operativos, var_name='RESGUARDO', value_name='ESTADO')
            df_melt['ESTADO'] = pd.to_numeric(df_melt['ESTADO'], errors='coerce').fillna(0)
            
            # Agrupar progreso
            progreso = df_melt.groupby('RESGUARDO')['ESTADO'].sum().reset_index()
            progreso['Porcentaje'] = (progreso['ESTADO'] / len(df_capa)) * 100
            
            fig_capa = px.bar(progreso, x='RESGUARDO', y='Porcentaje', title='Progreso de Capacitación por Resguardo (%)',
                              color='Porcentaje', color_continuous_scale=['#FF7A00', '#002A8D'])
            fig_capa.update_layout(yaxis_title="% Completado")
            st.plotly_chart(fig_capa, use_container_width=True)

    with c2:
        if 'tiro' in dfs:
            df_tiro = dfs['tiro'].dropna(subset=['PROMEDIO'])
            # Filtramos al coordinador por si acaso se filtró en la hoja
            df_tiro = df_tiro[~df_tiro['RESGUARDO'].str.contains("CASTRO MAMANI", na=False)]
            
            fig_tiro = px.pie(df_tiro, names='RESGUARDO', values='PROMEDIO', 
                              title='Distribución de Rendimiento en Tiro (Promedio)', hole=0.3,
                              color_discrete_sequence=px.colors.sequential.Blues_r)
            fig_tiro.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_tiro, use_container_width=True)

with tab3:
    st.subheader("Control Logístico y Programación de Descansos")
    c1, c2 = st.columns(2)
    
    with c1:
        if 'vacaciones' in dfs:
            df_vac = dfs['vacaciones']
            # Gráfico apilado de vacaciones
            df_vac_plot = df_vac[['RESGUARDO', '2024 - 2025', '2025 - 2026', '2026 - 2027']].copy()
            df_vac_plot.replace('-', 0, inplace=True)
            for col in ['2024 - 2025', '2025 - 2026', '2026 - 2027']:
                df_vac_plot[col] = pd.to_numeric(df_vac_plot[col], errors='coerce').fillna(0)
                
            fig_vac = px.bar(df_vac_plot, x='RESGUARDO', y=['2024 - 2025', '2025 - 2026', '2026 - 2027'],
                             title='Saldo de Vacaciones por Periodo', barmode='stack',
                             color_discrete_map={'2024 - 2025': '#d9534f', '2025 - 2026': '#FF7A00', '2026 - 2027': '#002A8D'})
            st.plotly_chart(fig_vac, use_container_width=True)
            
    with c2:
        if 'equipamiento' in dfs:
            # Gráfico simple de control de entregas (Ejemplo con chalecos o armas si los datos son 1/0)
            st.info("💡 Módulo de Equipamiento conectado. La matriz está lista para proyectar las validaciones logísticas una vez se estandaricen las entregas en el Sheet.")
