import streamlit as st
import pandas as pd

# 1. CONFIGURACIÓN DE LA PÁGINA (Pestaña del navegador)
st.set_page_config(page_title="Portal Ejecutivo | BCP - Liderman", page_icon="🛡️", layout="wide")

# 2. INYECCIÓN DE DISEÑO WEB (CSS) - Colores BCP (Azul y Naranja)
st.markdown("""
    <style>
        /* Títulos en Azul BCP */
        h1, h2, h3 {
            color: #002A8D !important; 
            font-family: 'Arial', sans-serif;
        }
        /* Botones Naranja BCP */
        div.stButton > button:first-child {
            background-color: #FF7800 !important;
            color: white !important;
            border-radius: 6px;
            border: none;
            font-weight: bold;
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
        }
        div.stButton > button:first-child:hover {
            background-color: #CC6000 !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        /* Tarjetas de Métricas */
        div[data-testid="stMetricValue"] {
            color: #002A8D !important;
            font-size: 2.5rem !important;
            font-weight: 800 !important;
        }
        /* Cajas de texto del Login */
        .stTextInput input {
            border-radius: 5px;
            border: 1px solid #002A8D;
        }
        /* Barra superior falsa para darle look de software BCP */
        .top-bar {
            background-color: #002A8D;
            padding: 10px;
            border-radius: 5px;
            color: white;
            text-align: center;
            font-weight: bold;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
    </style>
""", unsafe_allow_html=True)

# 3. CONTROL DE SESIÓN
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- PANTALLA DE LOGIN ---
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        st.markdown("<div class='top-bar'>PORTAL DE SEGURIDAD EJECUTIVA | CREDICORP</div>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center;'>LIDERMAN <span style='color:#FF7800;'>x</span> BCP</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Sistema de Gestión y Seguimiento Operativo Diario</p>", unsafe_allow_html=True)
        st.write("---")
        
        with st.form("login_form"):
            usuario = st.text_input("👤 Usuario (Pista: admin)")
            password = st.text_input("🔒 Contraseña (Pista: 123)", type="password")
            submit = st.form_submit_button("Ingresar al Portal 🚀")
            
            if submit:
                # Credenciales de prueba
                if usuario == "admin" and password == "123":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas. Verifique sus datos.")
                    
        st.markdown("<br><p style='text-align: center; color: #a0a0a0; font-size: 11px;'>© 2026 Banco de Crédito del Perú | J&V Resguardo S.A.C.<br>Confidencial - Solo para uso gerencial</p>", unsafe_allow_html=True)

# --- PANEL PRINCIPAL (DASHBOARD) ---
else:
    # Sidebar súper limpio
    st.sidebar.markdown("<h2 style='text-align: center;'>Módulos BCP</h2>", unsafe_allow_html=True)
    st.sidebar.write("---")
    menu = st.sidebar.radio(
        "Navegación Operativa:",
        ["📊 Resumen Ejecutivo", "🔫 Control de Armamento", "📑 Licencias SUCAMEC", "🏥 Salud Ocupacional (EMO)", "⚙️ Configuración"]
    )
    
    st.sidebar.write("---")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.rerun()

    # Pestaña 1: Resumen
    if menu == "📊 Resumen Ejecutivo":
        st.markdown("<div class='top-bar'>DASHBOARD GENERAL DE OPERACIONES - SETIEMBRE 2026</div>", unsafe_allow_html=True)
        
        # Tarjetas de KPI BCP Style
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric(label="👥 Personal Activo", value="9", delta="Escolta y G2-G7")
        with col2: st.metric(label="🎯 Armamento Completo", value="100%", delta="Verificado")
        with col3: st.metric(label="📚 Cumplimiento PAC", value="89%", delta="-1 Pendiente", delta_color="inverse")
        with col4: st.metric(label="🩺 EMOs Vigentes", value="77.8%", delta="1 Observado", delta_color="inverse")
        
        st.write("---")
        st.subheader("Últimas Alertas del Sistema")
        st.warning("⚠️ **Observación Médica:** Víctor Resurrección Morales - Pendiente interconsulta oftalmológica.")
        st.info("ℹ️ **Renovación SUCAMEC:** Manuel Saavedra Maurtua - Licencia por vencer en Feb 2027.")

    # Pestaña 2: Armamento (Ejemplo de tabla seria)
    elif menu == "🔫 Control de Armamento":
        st.markdown("<div class='top-bar'>INVENTARIO FÍSICO DE ARMAMENTO Y EQUIPOS</div>", unsafe_allow_html=True)
        st.write("Auditoría de asignación de equipos críticos para el servicio de resguardo.")
        
        # Data falsa para que se vea genial hoy
        data = {
            "Agente": ["Víctor Resurrección", "Jorge Bonilla", "Wismer Farfán", "Miguel Calle"],
            "Puesto": ["G2", "G2", "G4", "G4"],
            "Glock": ["✅ OK", "✅ OK", "✅ OK", "✅ OK"],
            "Munición": ["30", "30", "30", "30"],
            "Chaleco": ["✅ OK", "✅ OK", "✅ OK", "✅ OK"],
            "Funda Chaleco": ["✅ OK", "❌ FALTA", "✅ OK", "✅ OK"]
        }
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)

    # Las demás pestañas...
    else:
        st.title(menu)
        st.write("En construcción... Aquí conectaremos el Google Sheets en el siguiente paso. 🚀")
