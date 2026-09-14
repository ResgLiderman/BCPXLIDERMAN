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
    for hoja in ['equipamiento', 'capa']:
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
df_tiro = filtrar_df(dfs['tiro'][dfs['tiro']['RESGUARDO'] != coordinador]) if resguardo_seleccionado in ["Todos", coordinador] == False or resguardo_seleccionado == "Todos" else pd.DataFrame()

emo_riesgo = len(df_emo[df_emo['DÍAS RESTANTES'] < 30]) if not df_emo.empty else 0
suc_riesgo = len(df_suc[df_suc['DÍAS RESTANTES SUCAMEC'] < 30]) if not df_suc.empty else 0
promedio_tiro_global = df_tiro['PROMEDIO'].mean() if not df_tiro.empty and 'PROMEDIO' in df_tiro.columns else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Dotación Seleccionada</div><div class="kpi-value">{len(df_emo) if not df_emo.empty else 0}</div><div class="kpi-desc">Personal filtrado</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Alertas EMO (<30 Días)</div><div class="kpi-value alert-{"red" if emo_riesgo > 0 else "green"}">{emo_riesgo}</div><div class="kpi-desc">Riesgo médico</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Alertas SUCAMEC (<30 Días)</div><div class="kpi-value alert-{"red" if suc_riesgo > 0 else "green"}">{suc_riesgo}</div><div class="kpi-desc">Vencimientos legales</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Promedio Operativo (Tiro)</div><div class="kpi-value">{promedio_tiro_global:.1f}/20</div><div class="kpi-desc">Rendimiento Táctico Global</div></div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["⚖️ Legal y Médico (EMO/SUCAMEC)", "🎯 Táctico y Físico", "📦 Logística y Capacitación"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        if not df_emo.empty:
            df_plot = df_emo.sort_values('DÍAS RESTANTES', ascending=True).head(10)
            fig1 = px.bar(df_plot, x='DÍAS RESTANTES', y='RESGUARDO', orientation='h', text='DÍAS RESTANTES',
                          title="Vencimientos EMO (Críticos arriba)", color='DÍAS RESTANTES', color_continuous_scale=['#d9534f', '#FF7A00', '#002A8D'])
            fig1.add_vline(x=30, line_dash="dash", line_color="red")
            fig1.update_layout(yaxis={'categoryorder':'total descending'}, coloraxis_showscale=False)
            fig1.update_traces(textposition='outside', textfont_size=12, textfont_color='black')
            st.plotly_chart(fig1, use_container_width=True)
    with c2:
        if not df_suc.empty:
            df_plot = df_suc.sort_values('DÍAS RESTANTES SUCAMEC', ascending=True).head(10)
            fig2 = px.bar(df_plot, x='DÍAS RESTANTES SUCAMEC', y='RESGUARDO', orientation='h', text='DÍAS RESTANTES SUCAMEC',
                          title="Vencimientos Carné SUCAMEC", color='DÍAS RESTANTES SUCAMEC', color_continuous_scale=['#d9534f', '#FF7A00', '#002A8D'])
            fig2.add_vline(x=30, line_dash="dash", line_color="red")
            fig2.update_layout(yaxis={'categoryorder':'total descending'}, coloraxis_showscale=False)
            fig2.update_traces(textposition='outside')
            st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.markdown("**Evaluaciones Operativas (Excluye Coordinador)**")
    meses = ['ene-26', 'feb-26', 'mar-26', 'abr-26', 'may-26', 'jun-26', 'jul-26', 'ago-26']
    c1, c2, c3 = st.columns(3)
    
    def plot_eval(df, col_name, title):
        df_op = filtrar_df(df[df['RESGUARDO'] != coordinador]).dropna(subset=['PROMEDIO'])
        if df_op.empty: return None, None
        df_op['PROMEDIO'] = pd.to_numeric(df_op['PROMEDIO'], errors='coerce')
        fig = px.bar(df_op, x='RESGUARDO', y='PROMEDIO', text_auto='.2f', title=title, color='PROMEDIO', color_continuous_scale=['#FF7A00', '#002A8D'])
        fig.add_hline(y=14, line_dash="dash", line_color="red", annotation_text="Mínimo")
        fig.update_layout(coloraxis_showscale=False)
        fig.update_traces(textposition='outside')
        return fig, df_op[['RESGUARDO', 'PROMEDIO', 'OBS']].dropna(subset=['OBS'])

    with c1:
        if 'tiro' in dfs:
            f_tiro, obs_tiro = plot_eval(dfs['tiro'], 'PROMEDIO', 'Rendimiento: Tiro')
            if f_tiro: 
                st.plotly_chart(f_tiro, use_container_width=True)
                if not obs_tiro.empty: st.dataframe(obs_tiro, hide_index=True)
    with c2:
        if 'maniobra' in dfs:
            f_man, obs_man = plot_eval(dfs['maniobra'], 'PROMEDIO', 'Rendimiento: Maniobra')
            if f_man: 
                st.plotly_chart(f_man, use_container_width=True)
                if not obs_man.empty: st.dataframe(obs_man, hide_index=True)
    with c3:
        if 'apt_fisica' in dfs:
            f_apt, obs_apt = plot_eval(dfs['apt_fisica'], 'PROMEDIO', 'Rendimiento: Aptitud Física')
            if f_apt: 
                st.plotly_chart(f_apt, use_container_width=True)
                if not obs_apt.empty: st.dataframe(obs_apt, hide_index=True)

with tab3:
    c1, c2 = st.columns([1, 1])
    with c1:
        if 'capa_flat' in dfs:
            df_capa = dfs['capa_flat']
            df_capa = df_capa[df_capa['RESGUARDO'] != coordinador]
            df_capa = filtrar_df(df_capa)
            df_capa['VALOR'] = pd.to_numeric(df_capa['VALOR'], errors='coerce').fillna(0)
            avance = df_capa.groupby('RESGUARDO')['VALOR'].sum().reset_index()
            # Ajuste de porcentaje asumiendo total de cursos por resguardo
            total_cursos = len(df_capa['CURSO'].unique()) if 'CURSO' in df_capa.columns else 1
            avance['% Cumplido'] = (avance['VALOR'] / total_cursos) * 100
            
            fig_capa = px.bar(avance, x='RESGUARDO', y='% Cumplido', text_auto='.0f', title="Cumplimiento Capacitaciones (%)", color='% Cumplido', color_continuous_scale=['#FF7A00', '#002A8D'])
            fig_capa.update_traces(textposition='outside')
            fig_capa.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig_capa, use_container_width=True)
            
    with c2:
        if 'equipamiento_flat' in dfs:
            st.markdown("**Matriz de Equipamiento Operativo**")
            df_eq = dfs['equipamiento_flat']
            df_eq = filtrar_df(df_eq[df_eq['RESGUARDO'] != coordinador])
            if not df_eq.empty:
                # Pivotear de vuelta para visualización limpia
                df_eq_pivot = df_eq.pivot(index='RESGUARDO', columns=df_eq.columns[0], values='VALOR').fillna('-')
                st.dataframe(df_eq_pivot, use_container_width=True)
