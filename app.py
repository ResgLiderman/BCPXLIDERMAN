import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from st_aggrid import AgGrid, GridOptionsBuilder
from streamlit_echarts import st_echarts
from datetime import datetime
from streamlit_lottie import st_lottie
from supabase import create_client, Client # <-- NUEVA INTEGRACIÓN NÚCLEO

def cargar_animacion_hacker(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# ==========================================
# 1. CONFIGURACIÓN DEL CENTRO DE MANDO (PALANTIR STYLE)
# ==========================================
st.set_page_config(page_title="BCP Command Center | Operaciones", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

# Inyección de CSS de Alta Gama Corporativa
st.markdown("""
<style>
    .stApp { background-color: #F8FAFC; }
    
    /* Tarjetas KPI Superiores */
    .kpi-card { 
        background: linear-gradient(145deg, #ffffff, #f0f0f0);
        padding: 20px; 
        border-radius: 12px; 
        box-shadow: 5px 5px 15px rgba(0,0,0,0.05), -5px -5px 15px rgba(255,255,255,0.8); 
        border-left: 6px solid #002A8D; 
        margin-bottom: 20px; 
        text-align: center; 
        transition: transform 0.2s;
    }
    .kpi-card:hover { transform: translateY(-5px); }
    .kpi-title { color: #64748B; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;}
    .kpi-value { color: #0F172A; font-size: 2.2rem; font-weight: 900; margin: 10px 0; font-family: 'Inter', sans-serif;}
    .kpi-desc { font-size: 0.8rem; font-weight: 600; padding: 4px 8px; border-radius: 4px; display: inline-block;}
    
    /* Colores de Alerta */
    .bg-red { background-color: #FEE2E2; color: #DC2626; }
    .bg-green { background-color: #DCFCE7; color: #16A34A; }
    .bg-blue { background-color: #E0E7FF; color: #4F46E5; }
    
    /* Dossier Header */
    .dossier-header { background: #002A8D; color: white; padding: 20px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .dossier-name { font-size: 2rem; font-weight: 800; margin: 0; }
    .dossier-role { font-size: 1rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 2px;}
    
    div[data-testid="stSidebar"] { background-color: #0F172A; }
    div[data-testid="stSidebar"] * { color: #F8FAFC !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MOTOR SUPABASE & SISTEMA HÍBRIDO (DATA LAKE)
# ==========================================
# Inicializar Supabase encriptado desde st.secrets
@st.cache_resource
def init_supabase() -> Client:
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error("⚠️ Enlace con Base de Datos BCP-Liderman no establecido. Revisa st.secrets.")
        return None

supabase = init_supabase()

@st.cache_data(ttl=60) # TTL reducido a 60s preparándonos para el Tiempo Real
def cargar_datos():
    # MODO HÍBRIDO: Mientras pasamos las tablas a Supabase, mantenemos Sheets
    # como motor de respaldo para que la app no se caiga.
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
            # 1. INTERCEPTACIÓN SUPABASE: Si la tabla es 'equipamiento', leemos de la bóveda
            if nombre == 'equipamiento':
                respuesta = supabase.table('equipamiento').select('*').execute()
                df = pd.DataFrame(respuesta.data)
                
                if not df.empty:
                    # Mapeo explícito para garantizar que el renderizado encuentre las columnas
                    df = df.rename(columns={
                        'resguardo': 'RESGUARDO',
                        'equipo': 'EQUIPO',
                        'cantidad': 'CANTIDAD'
                    })
                else:
                    # Si Supabase está vacía, activamos el Fallback a Google Sheets
                    df = pd.read_csv(base_url + gid, header=1)
            else:
                # Las demás tablas siguen leyendo de Google Sheets por ahora
                df = pd.read_csv(base_url + gid, header=1)
                
            df.columns = df.columns.str.strip()
            if 'RESGUARDO' in df.columns:
                df['RESGUARDO'] = df['RESGUARDO'].astype(str).str.strip()
            dfs[nombre] = df
            
        except Exception as e:
            dfs[nombre] = pd.DataFrame()
            
    hoy = pd.Timestamp.today()

    # Motor de Fechas (EMO, SUCAMEC, VACACIONES)
    fechas_config = [
        ('emo', 'F. VENC. DE EMO', 'DÍAS RESTANTES'), 
        ('doc_sucamec', 'F. VENCIMIENTO CARNÉ SUCAMEC', 'DÍAS RESTANTES SUCAMEC'),
        ('lic_sucamec', 'F. DE VENCIMIENTO', 'DÍAS RESTANTES LICENCIA')
    ]
    for hoja, col_fecha, col_nueva in fechas_config:
        if hoja in dfs and col_fecha in dfs[hoja].columns:
            dfs[hoja][col_fecha] = pd.to_datetime(dfs[hoja][col_fecha], format='%d/%m/%Y', errors='coerce')
            dfs[hoja][col_nueva] = (dfs[hoja][col_fecha] - hoy).dt.days

    # Aplanado Matricial Capacitaciones
    if 'capa' in dfs and not dfs['capa'].empty:
        col_id = dfs['capa'].columns[0]
        cols_res = [c for c in dfs['capa'].columns if c not in [col_id, 'Trimestre', 'TOTAL CURSOS COMPLETADOS'] and not c.startswith('Unnamed')]
        dfs['capa_flat'] = dfs['capa'].melt(id_vars=[col_id], value_vars=cols_res, var_name='RESGUARDO', value_name='VALOR')

    return dfs

dfs = cargar_datos()
coordinador = "CASTRO MAMANI, VICTOR"
lista_resguardos = dfs['emo']['RESGUARDO'].dropna().unique().tolist() if 'emo' in dfs and not dfs['emo'].empty else []

# ==========================================
# 3. SISTEMA DE FILTRADO TÁCTICO (SIDEBAR)
# ==========================================
st.sidebar.markdown('<div style="text-align: center;"><img src="https://upload.wikimedia.org/wikipedia/commons/0/0d/Logo-bcp-vector.svg" width="180"></div>', unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.title("⚙️ Filtro Operativo")
resguardo_seleccionado = st.sidebar.radio("Fijar Objetivo (Resguardo):", ["Todos"] + lista_resguardos)

radar_url = "https://lottie.host/7c7328bf-4277-4011-a54c-1123f13fb46e/a70i3dXVGk.json"
animacion_radar = cargar_animacion_hacker(radar_url)

if animacion_radar:
    with st.sidebar:
        st_lottie(animacion_radar, height=150, key="radar_seguridad")

def filtrar_df(df, col='RESGUARDO'):
    if resguardo_seleccionado == "Todos":
        return df
    return df[df[col] == resguardo_seleccionado] if col in df.columns else df

def obtener_nota_segura(hoja):
    if hoja not in dfs or dfs[hoja].empty: return 0.0
    df_temp = filtrar_df(dfs[hoja][dfs[hoja]['RESGUARDO'] != coordinador])
    if df_temp.empty or 'PROMEDIO' not in df_temp.columns: return 0.0
    notas = pd.to_numeric(df_temp['PROMEDIO'], errors='coerce').dropna()
    return notas.mean() if not notas.empty else 0.0

# ==========================================
# 4. VISTA DE DOSSIER EJECUTIVO (MODAL INTEGRADO)
# ==========================================
if resguardo_seleccionado != "Todos":
    nota_t = obtener_nota_segura('tiro')
    nota_m = obtener_nota_segura('maniobra')
    nota_f = obtener_nota_segura('apt_fisica')
    prom_global_indiv = (nota_t + nota_m + nota_f) / 3

    st.markdown(f"""
    <div class="dossier-header">
        <h1 class="dossier-name">👤 {resguardo_seleccionado}</h1>
        <p class="dossier-role">RESGUARDO OPERATIVO LIDERMAN | ESTADO GLOBAL: {'🔴 EN RIESGO' if prom_global_indiv < 15 else '🟢 ÓPTIMO'}</p>
    </div>
    """, unsafe_allow_html=True)

    d_col1, d_col2 = st.columns([1, 2])
    
    with d_col1:
        st.markdown("**🕷️ Perfil Táctico (Spider Chart)**")
        options = {
            "tooltip": {},
            "legend": {"data": ["Desempeño Actual", "Umbral Mínimo", "Estándar BCP"], "bottom": 0},
            "radar": {
                "indicator": [
                    {"name": '🎯 Tiro', "max": 20},
                    {"name": '🏃 Física', "max": 20},
                    {"name": '🛡️ Maniobra', "max": 20}
                ],
                "splitArea": { "areaStyle": { "color": ['#f8fafc', '#f1f5f9'] } }
            },
            "series": [{
                "name": "Perfil Operativo",
                "type": 'radar',
                "data": [
                    { "value": [nota_t, nota_f, nota_m], "name": "Desempeño Actual", "itemStyle": {"color": "#002A8D"}, "areaStyle": {"opacity": 0.4} },
                    { "value": [15, 15, 15], "name": "Umbral Mínimo", "itemStyle": {"color": "#DC2626"}, "lineStyle": {"type": 'dashed'} },
                    { "value": [20, 20, 20], "name": "Estándar BCP", "itemStyle": {"color": "#10B981"}, "lineStyle": {"type": 'dotted'} }
                ]
            }]
        }
        st_echarts(options, height="350px")

    with d_col2:
        st.markdown("**📋 Resumen 360**")
        df_emo_ind = filtrar_df(dfs.get('emo', pd.DataFrame()))
        df_vac_ind = filtrar_df(dfs.get('vacaciones', pd.DataFrame()))
        
        dias_emo = int(df_emo_ind['DÍAS RESTANTES'].iloc[0]) if not df_emo_ind.empty and 'DÍAS RESTANTES' in df_emo_ind.columns else "N/D"
        vac_text = df_vac_ind['OBSERVACIÓN'].iloc[0] if not df_vac_ind.empty and 'OBSERVACIÓN' in df_vac_ind.columns else "Sin incidencias"
        
        st.info(f"**🩺 Estado Médico (EMO):** Vence en {dias_emo} días.")
        st.warning(f"**🌴 Novedades RRHH:** {vac_text}")
        st.metric(label="PROMEDIO TÁCTICO GLOBAL", value=f"{prom_global_indiv:.2f}/20", delta="- Brecha" if prom_global_indiv < 15 else "+ Apto", delta_color="inverse")
    
    st.markdown("---")

# ==========================================
# 5. DASHBOARD GLOBAL Y KPIs
# ==========================================
df_emo = filtrar_df(dfs.get('emo', pd.DataFrame()))
df_suc = filtrar_df(dfs.get('doc_sucamec', pd.DataFrame()))

emo_riesgo = len(df_emo[df_emo['DÍAS RESTANTES'] < 30]) if not df_emo.empty else 0
suc_riesgo = len(df_suc[df_suc['DÍAS RESTANTES SUCAMEC'] < 30]) if not df_suc.empty else 0

nota_tiro = obtener_nota_segura('tiro')
nota_maniobra = obtener_nota_segura('maniobra')
nota_fisico = obtener_nota_segura('apt_fisica')

etiq_kpi = "Nota" if resguardo_seleccionado != "Todos" else "Prom. Grupal"

k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1: st.markdown(f'<div class="kpi-card"><div class="kpi-title">Dotación</div><div class="kpi-value">{len(df_emo)}</div><div class="kpi-desc bg-blue">Efectivos</div></div>', unsafe_allow_html=True)
with k2: st.markdown(f'<div class="kpi-card"><div class="kpi-title">Alerta EMO</div><div class="kpi-value">{"0" if emo_riesgo==0 else emo_riesgo}</div><div class="kpi-desc {"bg-red" if emo_riesgo > 0 else "bg-green"}">Vencimientos</div></div>', unsafe_allow_html=True)
with k3: st.markdown(f'<div class="kpi-card"><div class="kpi-title">Alerta SUCAMEC</div><div class="kpi-value">{"0" if suc_riesgo==0 else suc_riesgo}</div><div class="kpi-desc {"bg-red" if suc_riesgo > 0 else "bg-green"}">Vencimientos</div></div>', unsafe_allow_html=True)
with k4: st.markdown(f'<div class="kpi-card"><div class="kpi-title">{etiq_kpi} Tiro</div><div class="kpi-value">{nota_tiro:.1f}</div><div class="kpi-desc {"bg-red" if nota_tiro < 15.0 else "bg-green"}">Táctico</div></div>', unsafe_allow_html=True)
with k5: st.markdown(f'<div class="kpi-card"><div class="kpi-title">{etiq_kpi} Maniobra</div><div class="kpi-value">{nota_maniobra:.1f}</div><div class="kpi-desc {"bg-red" if nota_maniobra < 15.0 else "bg-green"}">Táctico</div></div>', unsafe_allow_html=True)
with k6: st.markdown(f'<div class="kpi-card"><div class="kpi-title">{etiq_kpi} Físico</div><div class="kpi-value">{nota_fisico:.1f}</div><div class="kpi-desc {"bg-red" if nota_fisico < 15.0 else "bg-green"}">Táctico</div></div>', unsafe_allow_html=True)

# ==========================================
# 6. CENTRO DE CONTROL (TABS)
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Panel Táctico", "⚖️ Legal & RRHH", "📦 Logística", "🎓 Capacitaciones"])

with tab1:
    st.markdown("<h4 style='color: #002A8D;'>🔍 Matriz Consolidada de Riesgo Operativo (Ag-Grid)</h4>", unsafe_allow_html=True)
    
    df_lista = []
    for hoja in ['tiro', 'maniobra', 'apt_fisica']:
        if hoja in dfs and not dfs[hoja].empty:
            df_temp = filtrar_df(dfs[hoja][dfs[hoja]['RESGUARDO'] != coordinador]).copy()
            if 'PROMEDIO' in df_temp.columns:
                df_temp['PROMEDIO'] = pd.to_numeric(df_temp['PROMEDIO'], errors='coerce')
                col_obs = 'OBSERVACIÓN' if 'OBSERVACIÓN' in df_temp.columns else ('OBS' if 'OBS' in df_temp.columns else None)
                if col_obs:
                    df_lista.append(df_temp[['RESGUARDO', 'PROMEDIO', col_obs]].rename(columns={col_obs: 'OBSERVACIÓN'}))
    
    if df_lista:
        df_concat = pd.concat(df_lista, ignore_index=True)
        df_panel = df_concat.groupby('RESGUARDO').agg({
            'PROMEDIO': 'mean',
            'OBSERVACIÓN': lambda x: ' | '.join([str(i) for i in x.dropna().unique() if str(i).strip() != ''])
        }).reset_index()
        
        df_panel['PROM. GLOBAL'] = df_panel['PROMEDIO'].round(2)
        df_aggrid = df_panel[['RESGUARDO', 'PROM. GLOBAL', 'OBSERVACIÓN']].copy()
        df_aggrid['ESTADO'] = ['🔴 ALERTA TÁCTICA' if x < 15.0 else '🟢 APTO' for x in df_aggrid['PROM. GLOBAL']]
        
        gb = GridOptionsBuilder.from_dataframe(df_aggrid)
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_side_bar() 
        gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='sum', editable=False, filter=True)
        gb.configure_column("RESGUARDO", width=250, pinned="left")
        gb.configure_column("PROM. GLOBAL", type=["numericColumn"], width=130)
        gb.configure_column("OBSERVACIÓN", width=400)
        
        gridOptions = gb.build()
        AgGrid(df_aggrid, gridOptions=gridOptions, enable_enterprise_modules=False, theme="balham", height=350, fit_columns_on_grid_load=True)

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    def plot_eval(df, title):
        df_base = df[df['RESGUARDO'] != coordinador].dropna(subset=['PROMEDIO']).copy()
        df_base['PROMEDIO'] = pd.to_numeric(df_base['PROMEDIO'], errors='coerce')
        df_op = filtrar_df(df_base)
        if df_op.empty: return None
        
        if len(df_op) == 1 and resguardo_seleccionado != "Todos":
            df_plot = pd.DataFrame({
                'RESGUARDO': [df_op['RESGUARDO'].iloc[0], 'MEDIA GRUPAL'],
                'PROMEDIO': [df_op['PROMEDIO'].iloc[0], df_base['PROMEDIO'].mean()],
                'ESTADO': ['Riesgo (<15.0)' if df_op['PROMEDIO'].iloc[0] < 15.0 else 'Óptimo', 'Benchmark']
            })
        else:
            df_plot = df_op.copy()
            df_plot['ESTADO'] = ['Riesgo (<15.0)' if x < 15.0 else 'Óptimo' for x in df_plot['PROMEDIO']]
            
        fig = px.bar(df_plot, x='RESGUARDO', y='PROMEDIO', text_auto='.2f', title=title, 
                     color='ESTADO', color_discrete_map={'Riesgo (<15.0)': '#d9534f', 'Óptimo': '#002A8D', 'Benchmark': '#94A3B8'})
        fig.add_hline(y=15, line_dash="dash", line_color="#D97706")
        fig.update_traces(textangle=0, textposition='outside') # <-- BLOQUEO VERTICAL DE NÚMEROS APLICADO
        fig.update_layout(showlegend=False, yaxis_range=[0, 24])
        return fig

    with c1:
        if 'tiro' in dfs:
            f_tiro = plot_eval(dfs['tiro'], 'Desempeño: Tiro')
            if f_tiro: st.plotly_chart(f_tiro, use_container_width=True)
    with c2:
        if 'maniobra' in dfs:
            f_man = plot_eval(dfs['maniobra'], 'Desempeño: Maniobra')
            if f_man: st.plotly_chart(f_man, use_container_width=True)
    with c3:
        if 'apt_fisica' in dfs:
            f_apt = plot_eval(dfs['apt_fisica'], 'Desempeño: Apt. Física')
            if f_apt: st.plotly_chart(f_apt, use_container_width=True)

with tab2:
    v1, v2 = st.columns(2)
    with v1:
        if 'emo' in dfs and not dfs['emo'].empty:
            df_plot = filtrar_df(dfs['emo']).sort_values('DÍAS RESTANTES').head(10)
            fig1 = px.bar(df_plot, x='DÍAS RESTANTES', y='RESGUARDO', orientation='h', title="Top Vencimientos EMO", 
                          color=['Crítico' if x<30 else 'Vigente' for x in df_plot['DÍAS RESTANTES']],
                          color_discrete_map={'Crítico': '#d9534f', 'Vigente': '#002A8D'})
            fig1.add_vline(x=30, line_dash="solid", line_color="black")
            st.plotly_chart(fig1, use_container_width=True)
            
    with v2:
        if 'vacaciones' in dfs and not dfs['vacaciones'].empty:
            st.markdown("**🌴 Registro de Vacaciones (RRHH)**")
            df_vac = filtrar_df(dfs['vacaciones'])
            cols_seguras = [c for c in ['RESGUARDO', 'OBSERVACIÓN', 'OBS'] if c in df_vac.columns]
            
            if cols_seguras:
                st.dataframe(df_vac[cols_seguras], use_container_width=True, hide_index=True)
            else:
                st.dataframe(df_vac, use_container_width=True, hide_index=True)

with tab3:
    st.markdown("**📦 Módulo Logístico y Control de Activos**")
    if 'equipamiento' in dfs and not dfs['equipamiento'].empty:
        df_eq = dfs['equipamiento'].copy().dropna(subset=['EQUIPO'])
        
        # MOTOR INTELIGENTE: Detectar si es Base de Datos (Supabase) o Matriz (Google Sheets)
        if 'RESGUARDO' in df_eq.columns:
            # LÓGICA NUEVA: Formato Base de Datos (Vertical)
            if resguardo_seleccionado != "Todos":
                df_eq = df_eq[df_eq['RESGUARDO'] == resguardo_seleccionado]
            st.dataframe(df_eq[['RESGUARDO', 'CANTIDAD', 'EQUIPO']], hide_index=True, use_container_width=True)
            
        else:
            # LÓGICA ANTIGUA: Formato Google Sheets (Horizontal con melt)
            cols_resguardos = [c for c in df_eq.columns if ',' in str(c) and c != coordinador]
            if resguardo_seleccionado != "Todos" and resguardo_seleccionado in df_eq.columns:
                st.dataframe(df_eq[['CANTIDAD', 'EQUIPO', resguardo_seleccionado]], hide_index=True, use_container_width=True)
            else:
                df_eq_vertical = df_eq.melt(id_vars=['EQUIPO', 'CANTIDAD'], value_vars=cols_resguardos, var_name='RESGUARDO', value_name='ASIGNADO')
                df_eq_vertical = df_eq_vertical[pd.to_numeric(df_eq_vertical['ASIGNADO'], errors='coerce').fillna(0) > 0]
                st.dataframe(df_eq_vertical[['RESGUARDO', 'CANTIDAD', 'EQUIPO']], hide_index=True, use_container_width=True)
with tab4:
    if 'capa_flat' in dfs and not dfs['capa_flat'].empty:
        df_capa = dfs['capa_flat'].copy()
        df_capa = df_capa[(df_capa['RESGUARDO'] != coordinador) & (~df_capa['RESGUARDO'].isin(['CURSO', 'TOTAL', 'Trimestre']))]
        df_capa = filtrar_df(df_capa)
        df_capa['VALOR'] = pd.to_numeric(df_capa['VALOR'], errors='coerce').fillna(0)
        avance = df_capa.groupby('RESGUARDO')['VALOR'].sum().reset_index()
        avance['% Cumplido'] = (avance['VALOR'] / 16) * 100
        avance['% Cumplido'] = avance['% Cumplido'].apply(lambda x: 100 if x > 100 else x)
        fig_capa = px.bar(avance, x='RESGUARDO', y='% Cumplido', title="Avance de Capacitaciones (%)", color='% Cumplido', color_continuous_scale=['#FF7A00', '#002A8D'])
        fig_capa.update_layout(yaxis_range=[0, 115])
        fig_capa.update_traces(textangle=0, textposition='outside') # <-- SEGUNDO BLOQUEO DE NÚMEROS APLICADO
        st.plotly_chart(fig_capa, use_container_width=True)
