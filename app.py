import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

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

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        if not df_emo.empty:
            df_plot = df_emo.sort_values('DÍAS RESTANTES', ascending=True).head(10)
            # Semáforo binario: Rojo si <30, Azul BCP si >=30
            df_plot['ESTADO'] = ['Crítico (<30d)' if x < 30 else 'Vigente' for x in df_plot['DÍAS RESTANTES']]
            
            fig1 = px.bar(df_plot, x='DÍAS RESTANTES', y='RESGUARDO', orientation='h', text='DÍAS RESTANTES',
                          title="Vencimientos EMO (Críticos arriba)", color='ESTADO', 
                          color_discrete_map={'Crítico (<30d)': '#d9534f', 'Vigente': '#002A8D'})
            
            fig1.add_vline(x=30, line_dash="solid", line_color="#000000", line_width=3, annotation_text="Límite Crítico: 30d", annotation_position="top")
            fig1.update_layout(yaxis={'categoryorder':'total descending'}, showlegend=True, legend_title=None, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            fig1.update_traces(textposition='outside', textfont_size=12, textfont_color='black')
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
            fig2.update_traces(textposition='outside', textfont_size=12, textfont_color='black')
            st.plotly_chart(fig2, use_container_width=True)
            
with tab2:
    st.markdown("**Evaluaciones Operativas (Excluye Coordinador)**")
    c1, c2, c3 = st.columns(3)
    
    # Contenedor para agrupar todas las observaciones al final
    observaciones_globales = []
    
    def plot_eval(df, col_name, title, tipo_eval):
        df_op = filtrar_df(df[df['RESGUARDO'] != coordinador]).dropna(subset=['PROMEDIO'])
        if df_op.empty: return None
        
        df_op['PROMEDIO'] = pd.to_numeric(df_op['PROMEDIO'], errors='coerce')
        # Lógica de semáforo estricta al 15.0
        df_op['ESTADO'] = ['Riesgo (<15.0)' if x < 15.0 else 'Óptimo (>=15.0)' for x in df_op['PROMEDIO']]
        
        # Guardar observaciones justificadas para el panel inferior
        obs_df = df_op[['RESGUARDO', 'PROMEDIO', 'OBS']].dropna(subset=['OBS'])
        if not obs_df.empty:
            obs_df['EVALUACIÓN'] = tipo_eval
            observaciones_globales.append(obs_df)
            
        # El estándar mínimo pasa limpio al título
        fig = px.bar(df_op, x='RESGUARDO', y='PROMEDIO', text_auto='.2f', title=f"{title} (Mín: 15.0)", 
                     color='ESTADO', color_discrete_map={'Riesgo (<15.0)': '#d9534f', 'Óptimo (>=15.0)': '#002A8D'})
        
        # Línea de corte limpia de alta visibilidad (Cero textos superpuestos)
        fig.add_hline(y=15, line_dash="solid", line_color="#1E293B", line_width=2)
        
        # Control de "ladrillo gigante"
        ancho_barra = 0.3 if len(df_op) == 1 else None 
        
        fig.update_layout(showlegend=False, yaxis_range=[0, 21])
        fig.update_traces(textposition='outside', width=ancho_barra)
        return fig

    with c1:
        if 'tiro' in dfs:
            f_tiro = plot_eval(dfs['tiro'], 'PROMEDIO', 'Rendimiento: Tiro', 'Tiro')
            if f_tiro: st.plotly_chart(f_tiro, use_container_width=True)
    with c2:
        if 'maniobra' in dfs:
            f_man = plot_eval(dfs['maniobra'], 'PROMEDIO', 'Rendimiento: Maniobra', 'Maniobra')
            if f_man: st.plotly_chart(f_man, use_container_width=True)
    with c3:
        if 'apt_fisica' in dfs:
            f_apt = plot_eval(dfs['apt_fisica'], 'PROMEDIO', 'Rendimiento: Aptitud Física', 'Aptitud Física')
            if f_apt: st.plotly_chart(f_apt, use_container_width=True)
            
    # PANEL UNIFICADO DE EXCEPCIONES OPERATIVAS (Adiós a las tablitas feas)
    if observaciones_globales:
        st.markdown("---")
        st.markdown("<h4 style='color: #d9534f;'>⚠️ Panel de Excepciones y Justificaciones</h4>", unsafe_allow_html=True)
        df_obs_total = pd.concat(observaciones_globales, ignore_index=True)
        # Reordenamos columnas para la vista gerencial
        df_obs_total = df_obs_total[['RESGUARDO', 'EVALUACIÓN', 'PROMEDIO', 'OBS']]
        st.dataframe(df_obs_total, use_container_width=True, hide_index=True)

with tab3:
    c1, c2 = st.columns([1, 1])
    with c1:
        if 'capa_flat' in dfs:
            df_capa = dfs['capa_flat'].copy()
            # Filtro destructor de basura: Quitar al coordinador y la palabra fantasma "CURSO" del eje
            df_capa = df_capa[(df_capa['RESGUARDO'] != coordinador) & 
                              (~df_capa['RESGUARDO'].isin(['CURSO', 'TOTAL', 'Trimestre']))]
            
            df_capa = filtrar_df(df_capa)
            df_capa['VALOR'] = pd.to_numeric(df_capa['VALOR'], errors='coerce').fillna(0)
            
            avance = df_capa.groupby('RESGUARDO')['VALOR'].sum().reset_index()
            # Calculamos base estricta de cursos (suponiendo que son 4 módulos)
            total_cursos_asignados = 16 # Ajusta este número si tu malla de cursos es distinta
            avance['% Cumplido'] = (avance['VALOR'] / total_cursos_asignados) * 100
            
            # Limitar a 100% máximo para evitar roturas visuales si hay datasucia
            avance['% Cumplido'] = avance['% Cumplido'].apply(lambda x: 100 if x > 100 else x)
            
            fig_capa = px.bar(avance, x='RESGUARDO', y='% Cumplido', text_auto='.0f', 
                              title="Cumplimiento Capacitaciones (%)", color='% Cumplido', 
                              color_continuous_scale=['#FF7A00', '#002A8D'])
            
            # Evitar ladrillo gigante al filtrar
            ancho_barra_capa = 0.3 if len(avance) == 1 else None
            
            fig_capa.update_traces(textposition='outside', width=ancho_barra_capa)
            fig_capa.update_layout(coloraxis_showscale=False, yaxis_range=[0, 115])
            st.plotly_chart(fig_capa, use_container_width=True)
            
    with c2:
        st.markdown("**Índice Logístico**")
        st.info("💡 Módulo de Control de Activos sincronizado. Revisa el detalle en el panel inferior.")
        
    # ACORDEÓN EXPANDIBLE FULL-WIDTH (Adiós al estrangulamiento visual de la tabla)
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
