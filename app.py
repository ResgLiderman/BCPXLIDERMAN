import streamlit as st
import pandas as pd

st.set_page_config(page_title="Control Operativo | J&V Resguardo", layout="wide")

st.markdown("""
    <style>
        /* Tema Claro Corporativo */
        .stApp {
            background-color: #F4F6F9; /* Gris perla muy elegante para el fondo */
        }
        
        /* Caja del Login estilo Tarjeta Corporativa Blanca */
        [data-testid="stForm"] {
            background: #FFFFFF;
            border: 1px solid #E1E5EB;
            border-radius: 12px; 
            padding: 40px 30px;
            box-shadow: 0px 10px 30px rgba(0, 42, 141, 0.08); /* Sombra sutil y limpia */
        }
        
        /* Tipografía y colores base */
        h1, h2, h3, h4, h5 { font-family: 'Segoe UI', Tahoma, sans-serif !important; color: #002A8D !important; }
        p, label { color: #495057 !important; font-weight: 500; }
        
        /* Cajas de texto */
        .stTextInput input {
            background-color: #F8F9FA;
            border: 1px solid #CED4DA;
            color: #333333;
            border-radius: 6px;
        }
        .stTextInput input:focus {
            border-color: #002A8D;
            box-shadow: 0 0 0 0.2rem rgba(0, 42, 141, 0.15);
        }
        
        /* Botones */
        div.stButton > button {
            border-radius: 6px;
            width: 100%;
            font-size: 14px;
            font-weight: bold;
            padding: 0.6rem;
            transition: all 0.3s;
        }
        
        /* Botón Primario (Ingresar) - Azul Marino */
        div[data-testid="column"]:nth-child(1) div.stButton > button {
            background-color: #002A8D !important;
            color: white !important;
            border: none;
        }
        div[data-testid="column"]:nth-child(1) div.stButton > button:hover {
            background-color: #FF7800 !important; /* Toque naranja corporativo al pasar el mouse */
            color: white !important;
        }

        /* Botón Secundario (Solicitar) - Borde Azul */
        div[data-testid="column"]:nth-child(2) div.stButton > button {
            background-color: transparent !important;
            color: #002A8D !important;
            border: 1px solid #002A8D !important;
        }
        div[data-testid="column"]:nth-child(2) div.stButton > button:hover {
            background-color: #F4F6F9 !important;
        }
        
        /* Textos ejecutivos superiores */
        .top-label {
            text-align: center;
            color: #FF7800; /* Naranja BCP */
            font-weight: 700;
            font-size: 12px;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        
        .main-title {
            text-align: center; 
            font-size: 26px;
            font-weight: 800;
            color: #002A8D; /* Azul BCP */
            margin-bottom: 5px;
        }
        
        .sub-title { text-align: center; color: #6C757D; font-size: 14px; margin-bottom: 35px; }
        
        /* Footer Legal */
        .footer-text { 
            text-align: center; 
            color: #868E96 !important; 
            font-size: 11px; 
            margin-top: 40px; 
            font-weight: normal;
            line-height: 1.6;
        }
    </style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([2.5, 1.4, 2.5]) 
    
    with col2:
        st.write("<br><br>", unsafe_allow_html=True) # Espacio para centrar verticalmente
        st.markdown("<div class='top-label'>UNIDAD DE RESGUARDO EJECUTIVO</div>", unsafe_allow_html=True)
        st.markdown("<div class='main-title'>PORTAL DE CONTROL OPERATIVO</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-title'>Sistema Integrado de Gestión y Seguimiento</div>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.markdown("<h5 style='text-align: center; margin-bottom: 25px;'>Credenciales de Acceso</h5>", unsafe_allow_html=True)
            
            usuario = st.text_input("Usuario Corporativo")
            password = st.text_input("Contraseña", type="password")
            
            st.write("") 
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                submit = st.form_submit_button("Ingresar")
            with col_btn2:
                register = st.form_submit_button("Solicitar")
            
            if submit:
                if usuario == "admin" and password == "123":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Acceso denegado. Contacte al administrador.")
                    
        # Copyright actualizado con los requerimientos legales
        st.markdown("<div class='footer-text'>© 2026 J&V RESGUARDO S.A.C.<br>Uso estrictamente gerencial y confidencial.</div>", unsafe_allow_html=True)

else:
    st.sidebar.markdown("<h3 style='text-align: center;'>Módulos de Gestión</h3>", unsafe_allow_html=True)
    menu = st.sidebar.radio("Navegación:", ["Resumen Ejecutivo", "Control de Armamento", "Licencias SUCAMEC", "Salud Ocupacional (EMO)"])
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.rerun()

    if menu == "Resumen Ejecutivo":
        st.markdown("<div class='top-label'>DASHBOARD GENERAL DE OPERACIONES - SETIEMBRE 2026</div>", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Personal Activo", "9", "Escolta y G2-G7")
        col2.metric("Armamento", "100%", "Verificado")
        col3.metric("Cumplimiento PAC", "89%", "-1 Pendiente", delta_color="inverse")
        col4.metric("EMOs Vigentes", "77.8%", "1 Observado", delta_color="inverse")
