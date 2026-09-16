import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder

# CONFIGURACIÓN CORPORATIVA
st.set_page_config(page_title="Dashboard BI - Operaciones", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #F4F6F9; }
    .kpi-card { background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-left: 5px solid #002A8D; margin-bottom: 20px; text-align: center; }
    .kpi-title { color: #FF7A00; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; }
    .kpi-value { color: #002A8D; font-size: 2rem; font-weight: 800; margin: 5px 0; }
    .kpi-desc { font-size: 0.8rem; font-weight: 600; }
    .alert-red { color: #d9534f; } .alert-green { color: #5cb85c; }
    div[data-testid="stSidebar"] { background-color: #002A8D; }
    div[data-testid="stSidebar"] * { color: white !important; }
</style>
""", unsafe_allow_html=True)

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
        df = pd.read_csv(base_url + gid, header=1)
        df.columns = df.columns.str.strip()
        if 'RESGUARDO' in df.columns:
            df['RESGUARDO'] = df['RESGUARDO'].astype(str).str.strip()
        dfs[nombre] = df
        
    hoy = pd.Timestamp.today()

    # Procesamiento de Fechas
    for hoja, col_fecha, col_nueva in [('emo', 'F. VENC. DE EMO', 'DÍAS RESTANTES'), 
                                       ('doc_sucamec', 'F. VENCIMIENTO CARNÉ SUCAMEC', 'DÍAS RESTANTES SUCAMEC'),
                                       ('lic_sucamec', 'F. DE VENCIMIENTO', 'DÍAS RESTANTES LICENCIA')]:
        if hoja in dfs and col_fecha in dfs[hoja].columns:
            dfs[hoja][col_fecha] = pd.to_datetime(dfs[hoja][col_fecha], format='%d/%m/%Y', errors='coerce')
            dfs[hoja][col_nueva] = (dfs[hoja][col_fecha] - hoy).dt.days
            dfs[hoja][col_fecha + '_STR'] = dfs[hoja][col_fecha].dt.strftime('%m/%d/%Y')

    # Transposición de matrices matriciales (Equipamiento y Capa)
    for hoja in ['capa']:
        if hoja in dfs:
            col_id = dfs[hoja].columns[0]
            columnas_resguardos = [c for c in dfs[hoja].columns if c not in [col_id, 'Trimestre', 'TOTAL CURSOS COMPLETADOS'] and not c.startswith('Unnamed')]
            df_melt = dfs[hoja].melt(id_vars=[col_id], value_vars=columnas_resguardos, var_name='RESGUARDO', value_name='VALOR')
            dfs[f'{hoja}_flat'] = df_melt

    return dfs

dfs = cargar_datos()
coordinador = "CASTRO MAMANI, VICTOR"
lista_resguardos = dfs['emo']['RESGUARDO'].dropna().unique().tolist() if 'emo' in dfs else []

# BARRA LATERAL - FILTRO GLOBAL
st.sidebar.title("⚙️ Filtros")
resguardo_seleccionado = st.sidebar.selectbox("Seleccionar Resguardo:", ["Todos"] + lista_resguardos)

def filtrar_df(df, col='RESGUARDO'):
    if resguardo_seleccionado == "Todos":
        return df
    return df[df[col] == resguardo_seleccionado] if col in df.columns else df

# CÁLCULO DE MÉTRICAS GLOBALES
df_emo = filtrar_df(dfs['emo'])
df_suc = filtrar_df(dfs['doc_sucamec'])

emo_riesgo = len(df_emo[df_emo['DÍAS RESTANTES'] < 30]) if not df_emo.empty else 0
suc_riesgo = len(df_suc[df_suc['DÍAS RESTANTES SUCAMEC'] < 30]) if not df_suc.empty else 0

# Motor de cálculo seguro para las 3 disciplinas (Evita el bug del 0.0/20)
def obtener_nota_segura(hoja):
    if hoja not in dfs: return 0.0
    df_temp = filtrar_df(dfs[hoja][dfs[hoja]['RESGUARDO'] != coordinador])
    if df_temp.empty or 'PROMEDIO' not in df_temp.columns: return 0.0
    notas = pd.to_numeric(df_temp['PROMEDIO'], errors='coerce').dropna()
    return notas.mean() if not notas.empty else 0.0

nota_tiro = obtener_nota_segura('tiro')
nota_maniobra = obtener_nota_segura('maniobra')
nota_fisico = obtener_nota_segura('apt_fisica')

# Dinamismo de etiquetas: "Promedio" para todos, "Nota" para 1 persona
etiq_kpi = "Nota" if resguardo_seleccionado != "Todos" else "Prom. Grupal"

# 6 TARJETAS DE ALTO IMPACTO EN FILA
col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Dotación</div><div class="kpi-value">{len(df_emo) if not df_emo.empty else 0}</div><div class="kpi-desc">Filtrada</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Alerta EMO</div><div class="kpi-value alert-{"red" if emo_riesgo > 0 else "green"}">{emo_riesgo}</div><div class="kpi-desc">< 30 Días</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Alerta SUCAMEC</div><div class="kpi-value alert-{"red" if suc_riesgo > 0 else "green"}">{suc_riesgo}</div><div class="kpi-desc">< 30 Días</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">{etiq_kpi} Tiro</div><div class="kpi-value alert-{"red" if nota_tiro < 15.0 else "green"}">{nota_tiro:.1f}</div><div class="kpi-desc">Táctico</div></div>', unsafe_allow_html=True)
with col5:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">{etiq_kpi} Maniob.</div><div class="kpi-value alert-{"red" if nota_maniobra < 15.0 else "green"}">{nota_maniobra:.1f}</div><div class="kpi-desc">Táctico</div></div>', unsafe_allow_html=True)
with col6:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">{etiq_kpi} Físico</div><div class="kpi-value alert-{"red" if nota_fisico < 15.0 else "green"}">{nota_fisico:.1f}</div><div class="kpi-desc">Táctico</div></div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["⚖️ Legal y Médico (EMO/SUCAMEC)", "🎯 Táctico y Físico", "📦 Logística y Capacitación"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        if not df_emo.empty:
            df_plot = df_emo.sort_values('DÍAS RESTANTES', ascending=True).head(10)
            df_plot['ESTADO'] = ['Crítico (<30d)' if x < 30 else 'Vigente' for x in df_plot['DÍAS RESTANTES']]
            
            fig1 = px.bar(df_plot, x='DÍAS RESTANTES', y='RESGUARDO', orientation='h', text='DÍAS RESTANTES',
                          title="Vencimientos EMO (Críticos arriba)", color='ESTADO', 
                          color_discrete_map={'Crítico (<30d)': '#d9534f', 'Vigente': '#002A8D'})
            
            fig1.add_vline(x=30, line_dash="solid", line_color="#000000", line_width=3, annotation_text="Límite Crítico: 30d", annotation_position="top")
            fig1.update_layout(yaxis={'categoryorder':'total descending'}, showlegend=True, legend_title=None, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            fig1.update_traces(textposition='outside', textfont_size=12, textfont_color='black', width=0.3 if len(df_plot) == 1 else None)
            st.plotly_chart(fig1, use_container_width=True)
    with c2:
        if not df_suc.empty:
            df_plot = df_suc.sort_values('DÍAS RESTANTES SUCAMEC', ascending=True).head(10)
            df_plot['ESTADO'] = ['Crítico (<30d)' if x < 30 else 'Vigente' for x in df_plot['DÍAS RESTANTES SUCAMEC']]
            
            fig2 = px.bar(df_plot, x='DÍAS RESTANTES SUCAMEC', y='RESGUARDO', orientation='h', text='DÍAS RESTANTES SUCAMEC',
                          title="Vencimientos Carné SUCAMEC", color='ESTADO', 
                          color_discrete_map={'Crítico (<30d)': '#d9534f', 'Vigente': '#002A8D'})
            
            fig2.add_vline(x=30, line_dash="solid", line_color="#000000", line_width=3, annotation_text="Límite Crítico: 30d", annotation_position="top")
            fig2.update_layout(yaxis={'categoryorder':'total descending'}, showlegend=True, legend_title=None, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            fig2.update_traces(textposition='outside', textfont_size=12, textfont_color='black', width=0.3 if len(df_plot) == 1 else None)
            st.plotly_chart(fig2, use_container_width=True)
            
with tab2:
    st.markdown("**Evaluaciones Operativas (Excluye Coordinador)**")
    c1, c2, c3 = st.columns(3)
    
    def plot_eval(df, col_name, title):
        df_base = df[df['RESGUARDO'] != coordinador].dropna(subset=['PROMEDIO']).copy()
        df_base['PROMEDIO'] = pd.to_numeric(df_base['PROMEDIO'], errors='coerce')
        media_grupal = df_base['PROMEDIO'].mean()
        
        df_op = filtrar_df(df_base)
        if df_op.empty: return None

        if len(df_op) == 1 and resguardo_seleccionado != "Todos":
            nota_indiv = df_op['PROMEDIO'].iloc[0]
            nombre_indiv = df_op['RESGUARDO'].iloc[0]
            df_plot = pd.DataFrame({
                'RESGUARDO': [nombre_indiv, 'MEDIA GRUPAL (BENCHMARK)'],
                'PROMEDIO': [nota_indiv, media_grupal],
                'ESTADO': ['Riesgo (<15.0)' if nota_indiv < 15.0 else 'Óptimo (>=15.0)', 'Benchmark']
            })
            ancho_barra = 0.4
        else:
            df_plot = df_op.copy()
            df_plot['ESTADO'] = ['Riesgo (<15.0)' if x < 15.0 else 'Óptimo (>=15.0)' for x in df_plot['PROMEDIO']]
            ancho_barra = None
            
        color_map = {'Riesgo (<15.0)': '#d9534f', 'Óptimo (>=15.0)': '#002A8D', 'Benchmark': '#94A3B8'}

        fig = px.bar(df_plot, x='RESGUARDO', y='PROMEDIO', text_auto='.2f', title=f"{title} (Mín: 15.0)", 
                     color='ESTADO', color_discrete_map=color_map)
        
        fig.add_hline(y=15, line_dash="dash", line_color="#D97706", line_width=2.5)
        fig.update_layout(showlegend=False, yaxis_range=[0, 24])
        fig.update_traces(textposition='outside', width=ancho_barra)
        return fig

    with c1:
        if 'tiro' in dfs:
            f_tiro = plot_eval(dfs['tiro'], 'PROMEDIO', 'Rendimiento: Tiro')
            if f_tiro: st.plotly_chart(f_tiro, use_container_width=True)
    with c2:
        if 'maniobra' in dfs:
            f_man = plot_eval(dfs['maniobra'], 'PROMEDIO', 'Rendimiento: Maniobra')
            if f_man: st.plotly_chart(f_man, use_container_width=True)
    with c3:
        if 'apt_fisica' in dfs:
            f_apt = plot_eval(dfs['apt_fisica'], 'PROMEDIO', 'Rendimiento: Aptitud Física')
            if f_apt: st.plotly_chart(f_apt, use_container_width=True)
            
    # PANEL CONSOLIDADO EJECUTIVO CON AG-GRID
    st.markdown("---")
    st.markdown("<h4 style='color: #002A8D;'>🔍 Panel de Control: Desviaciones y Ramp-Up Operativo</h4>", unsafe_allow_html=True)
    
    df_lista = []
    for hoja in ['tiro', 'maniobra', 'apt_fisica']:
        if hoja in dfs:
            df_temp = filtrar_df(dfs[hoja][dfs[hoja]['RESGUARDO'] != coordinador]).copy()
            if not df_temp.empty and 'PROMEDIO' in df_temp.columns:
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
        df_panel = df_panel[(df_panel['OBSERVACIÓN'] != '') | (df_panel['PROM. GLOBAL'] < 15.0)]
        
        if not df_panel.empty:
            # Preparamos el DataFrame final limpio para Ag-Grid
            df_aggrid = df_panel[['RESGUARDO', 'PROM. GLOBAL', 'OBSERVACIÓN']].copy()
            
            gb = GridOptionsBuilder.from_dataframe(df_aggrid)
            gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
            gb.configure_side_bar() # Habilita panel lateral de filtros y columnas
            gb.configure_default_column(editable=False, groupable=True, sortable=True, filterable=True)
            
            # Configuración específica de columnas y alineación
            gb.configure_column("RESGUARDO", headerName="RESGUARDO", width=280, pinned=True)
            gb.configure_column("PROM. GLOBAL", headerName="PROM. GLOBAL", width=140, type=["numericColumn"], precision=2)
            gb.configure_column("OBSERVACIÓN", headerName="OBSERVACIÓN / DIAGNÓSTICO", width=450)
            
            grid_options = gb.build()
            
            AgGrid(
                df_aggrid,
                gridOptions=grid_options,
                height=320,
                fit_columns_on_grid_load=True,
                theme="balham", # Tema corporativo limpio
                enable_enterprise_modules=False,
                allow_unsafe_jscode=True
            )
        else:
            st.success("✅ Toda la dotación cumple con el estándar y no presenta alertas operativas.")

with tab3:
    c1, c2 = st.columns([1, 1])
    with c1:
        if 'capa_flat' in dfs:
            df_capa = dfs['capa_flat'].copy()
            df_capa = df_capa[(df_capa['RESGUARDO'] != coordinador) & 
                              (~df_capa['RESGUARDO'].isin(['CURSO', 'TOTAL', 'Trimestre']))]
            
            df_capa = filtrar_df(df_capa)
            df_capa['VALOR'] = pd.to_numeric(df_capa['VALOR'], errors='coerce').fillna(0)
            
            avance = df_capa.groupby('RESGUARDO')['VALOR'].sum().reset_index()
            total_cursos_asignados = 16 
            avance['% Cumplido'] = (avance['VALOR'] / total_cursos_asignados) * 100
            
            avance['% Cumplido'] = avance['% Cumplido'].apply(lambda x: 100 if x > 100 else x)
            
            fig_capa = px.bar(avance, x='RESGUARDO', y='% Cumplido', text_auto='.0f', 
                            title="Cumplimiento Capacitaciones (%)", color='% Cumplido', 
                            color_continuous_scale=['#FF7A00', '#002A8D'])
            
            ancho_barra_capa = 0.3 if len(avance) == 1 else None
            
            fig_capa.update_traces(textposition='outside', width=ancho_barra_capa)
            fig_capa.update_layout(coloraxis_showscale=False, yaxis_range=[0, 115])
            st.plotly_chart(fig_capa, use_container_width=True)
            
    with c2:
        st.markdown("**Índice Logístico**")
        st.info("💡 Módulo de Control de Activos sincronizado. Revisa el detalle en el panel inferior.")
        
    st.markdown("---")
    if 'equipamiento' in dfs:
        with st.expander("📦 VER MATRIZ COMPLETA DE EQUIPAMIENTO OPERATIVO", expanded=False):
            df_eq = dfs['equipamiento'].copy()
            
            if 'EQUIPO' in df_eq.columns:
                df_eq = df_eq.dropna(subset=['EQUIPO'])
                cols_resguardos = [c for c in df_eq.columns if ',' in str(c)]
                
                if resguardo_seleccionado != "Todos" and resguardo_seleccionado in df_eq.columns:
                    st.dataframe(df_eq[['CANTIDAD', 'EQUIPO', resguardo_seleccionado]], hide_index=True, use_container_width=True)
                else:
                    cols_finales = ['CANTIDAD', 'EQUIPO'] + [c for c in cols_resguardos if c != coordinador]
                    st.dataframe(df_eq[[c for c in cols_finales if c in df_eq.columns]], hide_index=True, use_container_width=True)
