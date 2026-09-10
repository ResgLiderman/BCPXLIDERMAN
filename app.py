import streamlit as st
import pandas as pd

st.set_page_config(page_title="Portal Ejecutivo | BCP - Liderman", layout="wide")

st.markdown("""
    <style>
        /* Caja del Login con formato vertical tipo celular */
        [data-testid="stForm"] {
            background: linear-gradient(145deg, #1e2228, #191c21);
            border: 1px solid #2c323a;
            border-radius: 20px; /* Bordes más redondeados tipo móvil */
            padding: 40px 25px;
            box-shadow: 0px 20px 40px rgba(0, 0, 0, 0.7), 
                        0px 5px 15px rgba(0, 0, 0, 0.5);
        }
        
        h1, h2, h3, h4 { font-family: 'Segoe UI', Tahoma, sans-serif !important; }
        
        /* Botones estilo app */
        div.stButton > button {
            border-radius: 8px;
            border: none;
            width: 100%;
            font-size: 14px;
            font-weight: 600;
            padding: 0.5rem;
            transition: all 0.3s ease;
        }
        
        /* Botón Primario (Ingresar) */
        div[data-testid="column"]:nth-child(1) div.stButton > button {
            background-color: #002A8D !important;
            color: white !important;
            box-shadow: 0 4px 10px rgba(0, 42, 141, 0.4);
        }
        div[data-testid="column"]:nth-child(1) div.stButton > button:hover {
            background-color: #001f6b !important;
            transform: translateY(-2px);
        }

        /* Botón Secundario (Registro/Solicitar) */
        div[data-testid="column"]:nth-child(2) div.stButton > button {
            background-color: #2c323a !important;
            color: #A0AAB5 !important;
            border: 1px solid #4a5462 !important;
        }
        div[data-testid="column"]:nth-child(2) div.stButton > button:hover {
            background-color: #3b434f !important;
            color: white !important;
        }
        
        .top-bar {
            background-color: #002A8D;
            padding: 10px;
            border-radius: 6px;
            color: white;
            text-align: center;
            font-weight: 600;
            font-size: 12px;
            letter-spacing: 1.5px;
            margin-bottom: 30px;
        }
        
        .sub-title { text-align: center; color: #A0AAB5; font-size: 14px; margin-top: -10px; margin-bottom: 30px; }
        .footer-text { text-align: center; color: #5b6571; font-size: 11px; margin-top: 40px; }
    </style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    # AQUI ESTÁ LA MAGIA: 2.5 de espacio vacío, 1.2 para el celular, 2.5 de espacio vacío
    col1, col2, col3 = st.columns([2.5, 1.2, 2.5]) 
    
    with col2:
        st.markdown("<div class='top-bar'>CREDICORP</div>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #ffffff; letter-spacing: 1px;'>LIDERMAN <span style='color:#FF7800;'>x</span> BCP</h2>", unsafe_allow_html=True)
        st.markdown("<p class='sub-title'>Seguimiento Operativo</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.markdown("<h5 style='text-align: center; margin-bottom: 20px; color: #ffffff;'>Acceso Seguro</h5>", unsafe_allow_html=True)
            
            usuario = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            
            st.write("") # Espacio
            
            # Botones divididos a la mitad dentro del celular
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
                    st.error("Acceso denegado.")
                    
        st.markdown("<p class='footer-text'>© 2026 BCP | Liderman<br>Uso confidencial</p>", unsafe_allow_html=True)

else:
    st.sidebar.markdown("<h3 style='text-align: center; color: #002A8D;'>Módulos BCP</h3>", unsafe_allow_html=True)
    menu = st.sidebar.radio("Navegación:", ["Resumen Ejecutivo", "Control de Armamento", "Licencias SUCAMEC", "Salud Ocupacional (EMO)"])
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.rerun()

    if menu == "Resumen Ejecutivo":
        st.markdown("<div class='top-bar'>DASHBOARD GENERAL DE OPERACIONES - SETIEMBRE 2026</div>", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Personal Activo", "9", "Escolta y G2-G7")
        col2.metric("Armamento Completo", "100%", "Verificado")
        col3.metric("Cumplimiento PAC", "89%", "-1 Pendiente", delta_color="inverse")
        col4.metric("EMOs Vigentes", "77.8%", "1 Observado", delta_color="inverse")
