import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import base64
from st_aggrid import AgGrid, GridOptionsBuilder
from streamlit_echarts import st_echarts
from datetime import datetime
from streamlit_lottie import st_lottie
from supabase import create_client, Client # <-- NUEVA INTEGRACIÓN NÚCLEO

def cargar_img_local(ruta):
    try:
        with open(ruta, "rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    except:
        return ""

def cargar_animacion_hacker(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

st.markdown("""
<style>
/* Oculta la notificación molesta de "Running..." */
[data-testid="stStatusWidget"] {
    visibility: hidden;
    display: none;
}

/* Oculta el menú de los 3 puntos y elementos innecesarios */
#MainMenu {visibility: hidden;}
header .viewerBadge_container__1QSob {visibility: hidden;}

/* Forzar que el botón de expandir la barra lateral aparezca brillante y visible */
button[kind="header"] {
    visibility: visible !important;
    display: flex !important;
    z-index: 999999;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. CONFIGURACIÓN DEL CENTRO DE MANDO (PALANTIR STYLE)
# ==========================================
st.set_page_config(page_title="BCP Command Center | Operaciones", page_icon=cargar_img_local("BCPLOGO.png"), layout="wide", initial_sidebar_state="expanded")

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
@st.cache_resource(show_spinner=False)
def init_supabase() -> Client:
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error("⚠️ Enlace con Base de Datos BCP-Liderman no establecido. Revisa st.secrets.")
        return None

supabase = init_supabase()

@st.cache_data(ttl=1, show_spinner=False)
def cargar_datos():
    sheet_id = "1Cs3cV-NdVC6u1sDVhWEKpoP2OvDldzpWVIvx8bf-OSc"
    base_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid="
    
    # 1. ELIMINAMOS EQUIPAMIENTO DE GOOGLE SHEETS
    gids = {
        'doc_sucamec': '2135347375', 'lic_sucamec': '371955966',
        'capa': '1864610226', 'tiro': '1062108520', 'maniobra': '495125468',
        'apt_fisica': '2042184423', 'emo': '516174160', 'vacaciones': '1808970374'
    }
    
    dfs = {}
    
    # 2. EXTRACCIÓN PURA Y DIRECTA DE SUPABASE
    try:
        respuesta = supabase.table('equipamiento').select('*').execute()
        df_supa = pd.DataFrame(respuesta.data)
        if not df_supa.empty:
            df_supa = df_supa.rename(columns={'resguardo': 'RESGUARDO', 'equipo': 'EQUIPO', 'cantidad': 'CANTIDAD'})
        else:
            df_supa = pd.DataFrame(columns=['RESGUARDO', 'EQUIPO', 'CANTIDAD'])
        dfs['equipamiento'] = df_supa
    except Exception as e:
        dfs['equipamiento'] = pd.DataFrame(columns=['RESGUARDO', 'EQUIPO', 'CANTIDAD'])

    # 3. EXTRACCIÓN DEL RESTO EN SHEETS
    for nombre, gid in gids.items():
        try:
            df = pd.read_csv(base_url + gid, header=1)
            df.columns = df.columns.str.strip()
            if 'RESGUARDO' in df.columns:
                df['RESGUARDO'] = df['RESGUARDO'].astype(str).str.strip()
            dfs[nombre] = df
        except Exception as e:
            dfs[nombre] = pd.DataFrame()
            
    hoy = pd.Timestamp.today()
    fechas_config = [
        ('emo', 'F. VENC. DE EMO', 'DÍAS RESTANTES'), 
        ('doc_sucamec', 'F. VENCIMIENTO CARNÉ SUCAMEC', 'DÍAS RESTANTES SUCAMEC'),
        ('lic_sucamec', 'F. DE VENCIMIENTO', 'DÍAS RESTANTES LICENCIA')
    ]
    for hoja, col_fecha, col_nueva in fechas_config:
        if hoja in dfs and col_fecha in dfs[hoja].columns:
            dfs[hoja][col_fecha] = pd.to_datetime(dfs[hoja][col_fecha], format='%d/%m/%Y', errors='coerce')
            dfs[hoja][col_nueva] = (dfs[hoja][col_fecha] - hoy).dt.days

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
resguardo_seleccionado = st.sidebar.radio("Seleccionar Resguardo:", ["Todos"] + lista_resguardos)

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
        st.markdown("**Perfil Táctico**")
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
    st.markdown("<h4 style='color: #002A8D;'>Matriz Consolidada de las Operaciones</h4>", unsafe_allow_html=True)
    
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
            if resguardo_seleccionado == "Todos":
                df_plot = filtrar_df(dfs['emo']).sort_values('DÍAS RESTANTES').head(10)
                fig1 = px.bar(df_plot, x='DÍAS RESTANTES', y='RESGUARDO', orientation='h', title="Top Vencimientos EMO",  
                              color=['Crítico' if x<30 else 'Vigente' for x in df_plot['DÍAS RESTANTES']],
                              color_discrete_map={'Crítico': '#d9534f', 'Vigente': '#002A8D'})
                fig1.add_vline(x=30, line_dash="solid", line_color="black")
                st.plotly_chart(fig1, use_container_width=True)
            else:
                df_emo_ind = filtrar_df(dfs['emo'])
                st.markdown("**🩺 Control Médico EMO**")
                if not df_emo_ind.empty and 'DÍAS RESTANTES' in df_emo_ind.columns:
                    dias_restantes = int(df_emo_ind['DÍAS RESTANTES'].iloc[0])
                    color_badge = "bg-red" if dias_restantes < 30 else "bg-green"
                    estado_texto = "CRÍTICO - VENCE PRONTO" if dias_restantes < 30 else "VIGENTE"
                    
                    st.markdown(f"""
                    <div style="background: linear-gradient(145deg, #0F172A, #1E293B); padding: 30px; border-radius: 12px; text-align: center; border: 1px solid {'#DC2626' if dias_restantes < 30 else '#10B981'};">
                        <div style="color: #94A3B8; font-size: 0.8rem; font-weight: 700; letter-spacing: 1px; margin-bottom: 10px;">VENCIMIENTO DE EXAMEN MÉDICO (EMO)</div>
                        <div style="color: {'#DC2626' if dias_restantes < 30 else '#10B981'}; font-size: 3.5rem; font-weight: 900; font-family: 'Courier New', Courier, monospace;">{dias_restantes}</div>
                        <div style="color: #F8FAFC; font-size: 1rem; font-weight: 600; margin-top: 5px;">Días Restantes</div>
                        <div style="margin-top: 15px;"><span class="{color_badge}" style="padding: 6px 12px; border-radius: 6px; font-weight: 700; font-size: 0.85rem;">{estado_texto}</span></div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("Sin registros EMO para este operador.")
            
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
    if 'equipamiento' in dfs and not dfs['equipamiento'].empty:
        df_eq = dfs['equipamiento'].copy().dropna(subset=['EQUIPO'])

        if 'RESGUARDO' in df_eq.columns:
            df_eq['CANTIDAD'] = pd.to_numeric(df_eq['CANTIDAD'], errors='coerce').fillna(0)
            
            if resguardo_seleccionado != "Todos":
                # ==========================================
                # MODO 1: ESCÁNER BIOMÉTRICO INDIVIDUAL
                # ==========================================
                df_indiv = df_eq[df_eq['RESGUARDO'] == resguardo_seleccionado]
                
                if not df_indiv.empty:
                    st.markdown(f"<h4 style='color: #002A8D; border-bottom: 2px solid #FF7A00; padding-bottom: 10px; margin-bottom: 20px;'>Dotación EPP Asignada: {resguardo_seleccionado}</h4>", unsafe_allow_html=True)
                    cols = st.columns(min(len(df_indiv), 4))
                    for i, row in enumerate(df_indiv.itertuples()):
                        col_idx = i % 4
                        with cols[col_idx]:
                            st.markdown(f"""
                            <div style="background: linear-gradient(145deg, #0F172A, #1E293B); border: 1px solid #10B981; border-radius: 12px; padding: 30px 10px; text-align: center; box-shadow: 0 0 20px rgba(16, 185, 129, 0.15); margin-bottom: 15px;">
                                <div style="color: #94A3B8; font-size: 0.75rem; font-weight: 700; letter-spacing: 2px; margin-bottom: 10px;">ACTIVO ASIGNADO</div>
                                <h3 style="color: #10B981; font-size: 3.5rem; font-family: 'Courier New', Courier, monospace; margin: 0; text-shadow: 0 0 15px #10B981;">{int(row.CANTIDAD)}</h3>
                                <p style="color: #F8FAFC; font-size: 1.1rem; font-weight: 600; margin-top: 15px; text-transform: uppercase;">{row.EQUIPO}</p>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.info("💡 Operador táctico sin equipo asignado en la bóveda.")
                    
            else:
                # ==========================================
                # MODO 2: PANEL DE COMANDO CORPORATIVO
                # ==========================================
                c1, c2 = st.columns([1, 1.3])
                
                with c1:
                    total_resguardos = df_eq['RESGUARDO'].nunique()
                    st.markdown(f"""
                    <div style="background-color: #0F172A; padding: 40px 30px; border-radius: 16px; border-left: 6px solid #FF7A00; box-shadow: 0 10px 25px rgba(0,0,0,0.1); height: 100%;">
                        <h5 style="color: #94A3B8; text-transform: uppercase; letter-spacing: 2px; font-size: 0.9rem; margin-bottom: 20px;">Red Logística Activa</h5>
                        <h1 style="color: #F8FAFC; font-size: 5rem; margin: 0; line-height: 1;">{total_resguardos}</h1>
                        <p style="color: #FF7A00; font-weight: 600; font-size: 1.1rem; margin-top: 10px; text-transform: uppercase;">Total de Resguardos</p>
                        <hr style="border-color: #334155; margin: 25px 0;">
                        <p style="color: #CBD5E1; font-size: 0.85rem; line-height: 1.6;">Sincronización en tiempo real.</p>
                    </div>
                    """, unsafe_allow_html=True)

                with c2:
                    st.markdown(f"""
                    <div style="background: linear-gradient(145deg, #1E293B, #0F172A); padding: 40px 30px; border-radius: 16px; border-top: 6px solid #10B981; box-shadow: 0 10px 25px rgba(0,0,0,0.1); height: 100%;">
                        <h5 style="color: #94A3B8; text-transform: uppercase; letter-spacing: 2px; font-size: 0.9rem; margin-bottom: 20px;">Estado de armamento en campo.</h5>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                            <span style="color: #F8FAFC; font-size: 1.2rem; font-weight: 600;">Armamento Operativo</span>
                            <span style="color: #10B981; font-size: 1.5rem; font-weight: 900;">100%</span>
                        </div>
                        <div style="width: 100%; background-color: #334155; border-radius: 10px; height: 10px; margin-bottom: 30px;">
                            <div style="width: 100%; background-color: #10B981; height: 10px; border-radius: 10px; box-shadow: 0 0 10px #10B981;"></div>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                            <span style="color: #F8FAFC; font-size: 1.2rem; font-weight: 600;">Mantenimiento Preventivo</span>
                            <span style="color: #FF7A00; font-size: 1.5rem; font-weight: 900;">0%</span>
                        </div>
                        <div style="width: 100%; background-color: #334155; border-radius: 10px; height: 10px;">
                            <div style="width: 0%; background-color: #FF7A00; height: 10px; border-radius: 10px;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<hr style='border-color: #E2E8F0; margin: 40px 0;'>", unsafe_allow_html=True)

                # ========================================================
                # CÁPSULAS 2D LEVITANTES (BLINDADAS CON COMPONENTS.HTML)
                # ========================================================
                total_glock = int(df_eq[df_eq['EQUIPO'] == 'Glock 19']['CANTIDAD'].sum())
                total_cacerinas = int(df_eq[df_eq['EQUIPO'] == 'Cacerinas 9MM']['CANTIDAD'].sum())
                total_cartuchos = int(df_eq[df_eq['EQUIPO'] == 'Munición 9MM PB']['CANTIDAD'].sum())
                total_chaleco = int(df_eq[df_eq['EQUIPO'] == 'Chalecos Antibalas Ergonómico']['CANTIDAD'].sum())
                total_funda = int(df_eq[df_eq['EQUIPO'] == 'Fundas de Chaleco']['CANTIDAD'].sum())
                total_celular = int(df_eq[df_eq['EQUIPO'] == 'Teléfonos Móviles']['CANTIDAD'].sum())
                total_caja = int(df_eq[df_eq['EQUIPO'] == 'Cajas de Seguridad']['CANTIDAD'].sum())
                total_cartuchera = int(df_eq[df_eq['EQUIPO'] == 'Funda de Pistolas']['CANTIDAD'].sum())
                total_porta = int(df_eq[df_eq['EQUIPO'] == 'Porta Cacerinas']['CANTIDAD'].sum())
                total_fotochecks = int(df_eq[df_eq['EQUIPO'] == 'Fotochecks']['CANTIDAD'].sum())

                import streamlit.components.v1 as components
                holo1, holo2, holo3 = st.columns(3)

                def render_2d_capsule(img_url, main_count, color):
                    return f"""
                    <style>
                    @keyframes levitate {{
                        0% {{ transform: translateY(0px); }}
                        50% {{ transform: translateY(-12px); }}
                        100% {{ transform: translateY(0px); }}
                    }}
                    </style>
                    <div style="width: 250px; height: 250px; border-radius: 50%; background: radial-gradient(circle, rgba(15,23,42,0.8) 0%, rgba(15,23,42,1) 100%); border: 3px solid {color}; margin: 0 auto; position: relative; display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: 0 0 35px {color}60, inset 0 0 30px {color}20; overflow: hidden; font-family: sans-serif;">
                        
                        <!-- Resplandor trasero para matar el fondo oscuro -->
                        <div style="position: absolute; width: 140px; height: 140px; background: {color}; filter: blur(45px); opacity: 0.4; top: 15%;"></div>

                        <!-- Imagen PNG Levitando -->
                        <div style="animation: levitate 4s ease-in-out infinite; z-index: 5; margin-bottom: 10px;">
                            <img src="{img_url}" style="height: 110px; width: auto; max-width: 180px; object-fit: contain; filter: drop-shadow(0 15px 10px rgba(0,0,0,0.6));" />
                        </div>

                        <!-- Contador -->
                        <div style="position: absolute; bottom: 15px; color: #F8FAFC; font-weight: 900; font-size: 3.5rem; font-family: 'Courier New', Courier, monospace; line-height: 1; text-shadow: 0 0 15px {color}; z-index: 10;">{main_count}</div>
                    </div>
                    """

                with holo1:
                    st.markdown("<h3 style='text-align: center; color: #10B981; font-weight: 900; letter-spacing: 2px;'>ARMAMENTO</h3>", unsafe_allow_html=True)
                    # Llama a tu imagen guardada localmente
                    components.html(render_2d_capsule(cargar_img_local("glock_limpia.png"), total_glock, "#10B981"), height=270)
                with holo2:
                    st.markdown("<h3 style='text-align: center; color: #FF7A00; font-weight: 900; letter-spacing: 2px;'>PROTECCIÓN</h3>", unsafe_allow_html=True)
                    components.html(render_2d_capsule("https://pngimg.com/uploads/bulletproof_vest/bulletproof_vest_PNG44.png", total_chaleco, "#FF7A00"), height=270)

                with holo3:
                    st.markdown("<h3 style='text-align: center; color: #00E5FF; font-weight: 900; letter-spacing: 2px;'>ACCESORIOS</h3>", unsafe_allow_html=True)
                    # Llama a tu imagen guardada localmente
                    components.html(render_2d_capsule(cargar_img_local("maletin_limpio.png"), total_caja, "#00E5FF"), height=270)
                    
                st.markdown("<br><br>", unsafe_allow_html=True)

                # ========================================================
                # MODAL DE DESGLOSE (TABS NATIVAS - RENDIMIENTO 100%)
                # ========================================================
                
                def render_item(url_img, count, name, color):
                    return f"""
                    <div style='background: #FFFFFF; padding: 25px; border-radius: 12px; border: 2px solid {color}; text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; box-shadow: 0 10px 20px rgba(0,0,0,0.1);'>
                        <img src='{url_img}' style='height: 110px; max-width: 100%; object-fit: contain; margin-bottom: 20px;' />
                        <h2 style='color: {color}; margin: 0; font-size: 2.5rem; font-weight: 900;'>{count}</h2>
                        <p style='color: #0F172A; font-weight: 800; margin: 10px 0 0 0; font-size: 1.1rem; text-transform: uppercase;'>{name}</p>
                    </div>
                    """

                st.markdown("<h3 style='text-align: center; color: #002A8D; font-weight: 900; text-transform: uppercase; margin-bottom: 20px;'>Inventario y Dotación</h3>", unsafe_allow_html=True)
                
                tab_arm, tab_prot, tab_acc = st.tabs(["ARMAMENTO", "PROTECCIÓN", "ACCESORIOS"])
                
                with tab_arm:
                    st.markdown("<br>", unsafe_allow_html=True)
                    i1, i2, i3 = st.columns(3)
                    with i1:
                        st.markdown(render_item("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTU_L79X2myjyPYQgCNjDnsSuUvfYNLRFIqNuwvizxcGfzOZlului4-d8w&s=10", total_glock, "Glock 19", "#10B981"), unsafe_allow_html=True)
                    with i2:
                        st.markdown(render_item("https://www.tapperu.com/cdn/shop/files/MGGL33812_1_HR.jpg?v=1754591160", total_cacerinas, "Cacerinas 9MM", "#10B981"), unsafe_allow_html=True)
                    with i3:
                        st.markdown(render_item("https://www.indumil.gov.co/wp-content/uploads/2024/02/Municion_de_Defensa_Personal_03.png", total_cartuchos, "Munición 9MM PB", "#10B981"), unsafe_allow_html=True)
                
                with tab_prot:
                    st.markdown("<br>", unsafe_allow_html=True)
                    i1, i2 = st.columns(2)
                    with i1:
                        st.markdown(render_item("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSWBTRB7szjQBf8Xg50QUUs8tobt9uNpTeQ9kyrD6DYf2NX0laZjkJ7FNo&s=10", total_chaleco, "Chalecos Antibalas Ergónomico", "#FF7A00"), unsafe_allow_html=True)
                    with i2:
                        st.markdown(render_item("https://i.ytimg.com/vi/NUfdDG9M_PM/maxresdefault.jpg", total_funda, "Fundas de Chaleco", "#FF7A00"), unsafe_allow_html=True)
                
                with tab_acc:
                    st.markdown("<br>", unsafe_allow_html=True)
                    i1, i2, i3 = st.columns(3)
                    with i1:
                        st.markdown(render_item("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTw5DGcEpKZzlQ4kn65pfjxh7YZ1puRlAPOio-LCv65c1eEw7IB6Wwt5oJp&s=10", total_caja, "Cajas Seguridad", "#00E5FF"), unsafe_allow_html=True)
                    with i2:
                        st.markdown(render_item("https://rimage.ripley.com.pe/home.ripley/Attachment/WOP/1/2065374062748/image2-2065374062748.webp", total_celular, "Teléfonos Móviles", "#00E5FF"), unsafe_allow_html=True)
                    with i3:
                        st.markdown(render_item("https://images-na.ssl-images-amazon.com/images/I/61PkrqWoOaL._AC_UL495_SR435,495_.jpg", total_cartuchera, "Funda para Pistolas", "#00E5FF"), unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    _, i4, i5, _ = st.columns([0.5, 1, 1, 0.5])
                    with i4:
                        st.markdown(render_item("https://tactical.kipuasistente.com//files/imgarticulos/521-104.jpg", total_porta, "Porta Cacerinas", "#00E5FF"), unsafe_allow_html=True)
                    with i5:
                        st.markdown(f"""
                        <div style='background: #FFFFFF; padding: 25px; border-radius: 12px; border: 2px solid #00E5FF; text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; box-shadow: 0 10px 20px rgba(0,0,0,0.1);'>
                            <div style='font-size: 5rem; height: 110px; display: flex; align-items: center; margin-bottom: 20px;'>🪪</div>
                            <h2 style='color: #00E5FF; margin: 0; font-size: 2.5rem; font-weight: 900;'>{total_fotochecks}</h2>
                            <p style='color: #0F172A; font-weight: 800; margin: 10px 0 0 0; font-size: 1.1rem; text-transform: uppercase;'>Fotochecks</p>
                        </div>
                        """, unsafe_allow_html=True)

        else:
            cols_resguardos = [c for c in df_eq.columns if ',' in str(c) and c != coordinador]
            if resguardo_seleccionado != "Todos" and resguardo_seleccionado in df_eq.columns:
                st.dataframe(df_eq[['CANTIDAD', 'EQUIPO', resguardo_seleccionado]], hide_index=True, use_container_width=True)
            else:
                df_eq_vertical = df_eq.melt(id_vars=['EQUIPO', 'CANTIDAD'], value_vars=cols_resguardos, var_name='RESGUARDO', value_name='ASIGNADO')
                df_eq_vertical = df_eq_vertical[pd.to_numeric(df_eq_vertical['ASIGNADO'], errors='coerce').fillna(0) > 0]
                st.dataframe(df_eq_vertical[['RESGUARDO', 'CANTIDAD', 'EQUIPO']], hide_index=True, use_container_width=True)
    else:
        st.error("Bóveda de armería vacía o conexión interrumpida.")
        
with tab4:
    if 'capa_flat' in dfs and not dfs['capa_flat'].empty:
        df_capa = dfs['capa_flat'].copy()
        df_capa = df_capa[(df_capa['RESGUARDO'] != coordinador) & (~df_capa['RESGUARDO'].isin(['CURSO', 'TOTAL', 'Trimestre']))]
        df_capa = filtrar_df(df_capa)
        df_capa['VALOR'] = pd.to_numeric(df_capa['VALOR'], errors='coerce').fillna(0)
        avance = df_capa.groupby('RESGUARDO')['VALOR'].sum().reset_index()
        avance['% Cumplido'] = (avance['VALOR'] / 16) * 100
        avance['% Cumplido'] = avance['% Cumplido'].apply(lambda x: 100 if x > 100 else x)
        
        if resguardo_seleccionado == "Todos":
            fig_capa = px.bar(avance, x='RESGUARDO', y='% Cumplido', title="Avance de Capacitaciones (%)", color='% Cumplido', color_continuous_scale=['#FF7A00', '#002A8D'])
            fig_capa.update_layout(yaxis_range=[0, 115])
            fig_capa.update_traces(textangle=0, textposition='outside')
            st.plotly_chart(fig_capa, use_container_width=True)
        else:
            pct_val = float(avance['% Cumplido'].iloc[0]) if not avance.empty else 0.0
            color_capa = "#10B981" if pct_val >= 100 else "#FF7A00"
            st.markdown(f"""
            <div style="background: linear-gradient(145deg, #0F172A, #1E293B); padding: 40px; border-radius: 16px; text-align: center; border: 2px solid {color_capa}; box-shadow: 0 10px 25px rgba(0,0,0,0.1);">
                <div style="color: #94A3B8; font-size: 0.85rem; font-weight: 700; letter-spacing: 2px; margin-bottom: 15px;">ESTATUS DE CUMPLIMIENTO DE CAPACITACIONES</div>
                <div style="color: {color_capa}; font-size: 4.5rem; font-weight: 900; font-family: 'Courier New', Courier, monospace; text-shadow: 0 0 20px {color_capa}60;">{pct_val:.1f}%</div>
                <p style="color: #F8FAFC; font-size: 1.1rem; font-weight: 600; margin-top: 15px; text-transform: uppercase;">Avance de la malla curricular obligatoria</p>
            </div>
            """, unsafe_allow_html=True)
