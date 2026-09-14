import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA CORPORATIVA (Estilo BI)
st.set_page_config(
    page_title="Dashboard Ejecutivo - BCP", 
    page_icon="🛡️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. INYECCIÓN DE CSS PARA TARJETAS KPI (Look & Feel de alta gama)
st.markdown("""
<style>
    /* Fondo gris muy claro para resaltar las tarjetas blancas */
    .stApp {
        background-color: #F4F6F9;
    }
    /* Diseño de la tarjeta KPI */
    .kpi-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 5px solid #002A8D; /* Azul BCP */
        margin-bottom: 20px;
    }
    .kpi-title {
        color: #6c757d;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 10px;
    }
    .kpi-value {
        color: #1a1a1a;
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 5px;
    }
    .kpi-alert {
        font-size: 0.85rem;
        color: #d9534f;
        font-weight: 500;
    }
    .kpi-ok {
        font-size: 0.85rem;
        color: #5cb85c;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# 3. MOTOR DE EXTRACCIÓN DE DATOS (Caché para que sea rápido)
@st.cache_data(ttl=600) # Se actualiza cada 10 minutos
def cargar_datos():
    # El ID maestro de tu archivo
    sheet_id = "1Cs3cV-NdVC6u1sDVhWEKpoP2OvDldzpWVIvx8bf-OSc"
    base_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid="
    
    # Diccionario con los GIDs que me enviaste
    gids = {
        'equipamiento': '0',
        'doc_sucamec': '2135347375',
        'lic_sucamec': '371955966',
        'capa': '1864610226',
        'tiro': '1062108520',
        'maniobra': '495125468',
        'apt_fisica': '2042184423',
        'emo': '516174160',
        'vacaciones': '1808970374'
    }
    
    # Descarga de DataFrames
    dfs = {}
    for nombre, gid in gids.items():
        try:
            # MAGIA AQUÍ: header=1 le dice a Pandas que tus títulos están en la fila 2 del Excel
            dfs[nombre] = pd.read_csv(base_url + gid, header=1)
        except Exception as e:
            st.error(f"Error cargando la pestaña {nombre}: {e}")
            
    # --- PROCESAMIENTO NATIVO DE FECHAS (Ejemplo con ESTATUS EMO) ---
    if 'emo' in dfs:
        df_emo = dfs['emo'].copy()
        
        # Limpiar espacios en los nombres de las columnas por si acaso
        df_emo.columns = df_emo.columns.str.strip()
        
        # Convertir a formato fecha de Pandas
        df_emo['F. VENC. DE EMO'] = pd.to_datetime(df_emo['F. VENC. DE EMO'], format='%d/%m/%Y', errors='coerce')
        
        # Cálculo nativo de días restantes (Reemplaza la fórmula de Excel)
        hoy = pd.Timestamp.today()
        df_emo['DÍAS RESTANTES'] = (df_emo['F. VENC. DE EMO'] - hoy).dt.days
        
        # Formatear la fecha para que se vea como 05/24/2027 (mm/dd/yyyy) en la web
        df_emo['F. VENC. DE EMO_STR'] = df_emo['F. VENC. DE EMO'].dt.strftime('%m/%d/%Y')
        
        dfs['emo'] = df_emo

    return dfs

# 4. CARGA Y UI INICIAL
dfs = cargar_datos()

st.title("🛡️ Dashboard Ejecutivo de Operaciones")
st.markdown("Visión global de cumplimiento y estado logístico de los **resguardos**.")
st.markdown("---")

# Prueba rápida de conexión (Pintando una tarjeta KPI con datos de EMO)
if 'emo' in dfs:
    df_emo = dfs['emo']
    total_resguardos = len(df_emo)
    # Filtramos los que tienen menos de 30 días para vencer o ya vencieron
    alertas_emo = len(df_emo[df_emo['DÍAS RESTANTES'] < 30])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Universo de Resguardos</div>
            <div class="kpi-value">{total_resguardos}</div>
            <div class="kpi-ok">Dotación administrativa completa</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        alerta_clase = "kpi-alert" if alertas_emo > 0 else "kpi-ok"
        mensaje_alerta = f"⚠️ {alertas_emo} resguardos en riesgo" if alertas_emo > 0 else "✅ Cobertura médica óptima"
        
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Riesgo EMO (< 30 días)</div>
            <div class="kpi-value">{alertas_emo}</div>
            <div class="{alerta_clase}">{mensaje_alerta}</div>
        </div>
        """, unsafe_allow_html=True)

# Expander temporal para ver que la data plana entra perfecta
with st.expander("🔍 Ver estructura de datos crudos (Temporal para auditoría)"):
    st.dataframe(dfs['emo'][['RESGUARDO', 'F. VENC. DE EMO_STR', 'DÍAS RESTANTES', 'ESTATUS']])
