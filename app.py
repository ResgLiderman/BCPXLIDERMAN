import streamlit as st
import pandas as pd

st.set_page_config(page_title="Control Operativo | J&V Resguardo", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        /* 1. OCULTAR INTERFAZ NATIVA */
        header {visibility: hidden !important;}
        #MainMenu {visibility: hidden !important;}
        footer {visibility: hidden !important;}
        
        /* 2. FORZAR TEMA CLARO */
        .stApp { background-color: #F4F6F9 !important; }
        
        /* Fuentes solo para texto, evitando romper el ícono del ojito */
        h1, h2, h3, h4, h5, p, label { font-family: 'Segoe UI', Tahoma, sans-serif !important; }
        label { color: #495057 !important; font-weight: 600 !important; }
        
        /* 3. CAJA DEL LOGIN */
        [data-testid="stForm"] {
            background-color: #FFFFFF !important;
            border: 1px solid #E1E5EB !important;
            border-radius: 12px !important; 
            padding: 40px 30px !important;
            box-shadow: 0px 10px 30px rgba(0, 42, 141, 0.08) !important;
        }
        
        /* Solucionar el cuadro negro del ojito y la caja de texto completa */
        [data-testid="stTextInput"] div[data-baseweb="input"] {
            background-color: #F8F9FA !important;
            border: 1px solid #CED4DA !important;
            border-radius: 6px !important;
        }
        [data-testid="stTextInput"] input {
            color: #333333 !important;
            background-color: transparent !important; /* Deja ver el fondo claro */
        }
        
        /* 4. BOTONES (Soluciona el fondo negro forzando el color del texto interno) */
        div[data-testid="stForm"] button {
            border-radius: 6px !important;
            width: 100% !important;
            font-size: 14px !important;
            font-weight: bold !important;
            padding: 0.6rem !important;
        }
        
        /* Botón Ingresar */
        div[data-testid="column"]:nth-child(2) button {
            background-color: #002A8D !important;
            border: none !important;
        }
        div[data-testid="column"]:nth-child(2) button p { color: #FFFFFF !important; }
        div[data-testid="column"]:nth-child(2) button:hover { background-color: #FF7800 !important; }

        /* Botón Solicitar */
        div[data-testid="column"]:nth-child(3) button {
            background-color: transparent !important;
            border: 1px solid #002A8D !important;
        }
        div[data-testid="column"]:nth-child(3) button p { color: #002A8D !important; }
        div[data-testid="column"]:nth-child(3) button:hover { background-color: #F4F6F9 !important; }
        
        /* Textos */
        .top-label {
            text-align: center; color: #FF7800; font-weight: 700; font-size: 12px;
            letter-spacing: 2px; text-transform: uppercase; margin-bottom: 10px;
        }
        .main-title {
            text-align: center; font-size: 26px; font-weight: 800; color: #002A8D; margin-bottom: 5px;
        }
        .sub-title { text-align: center; color: #6C757D; font-size: 14px; margin-bottom: 35px; }
        .footer-text { 
            text-align: center; color: #868E96 !important; font-size: 11px; margin-top: 40px; line-height: 1.6;
        }
    </style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "vista" not in st.session_state:
    st.session_state.vista = "login"

if not st.session_state.logged_in:
    
    # --- PANTALLA DE SOLICITUD (REGISTRO) ---
    if st.session_state.vista == "registro":
        col1, col2, col3 = st.columns([2.5, 1.4, 2.5]) 
        with col2:
            st.write("<br><br>", unsafe_allow_html=True)
            st.markdown("<div class='main-title'>SOLICITUD DE ACCESO</div>", unsafe_allow_html=True)
            st.markdown("<div class='sub-title'>Registro de personal autorizado</div>", unsafe_allow_html=True)
            
            with st.form("registro_form"):
                nombre = st.text_input("Nombres y Apellidos")
                cargo = st.text_input("Cargo / Jefatura (Ej. Seguridad Ejecutiva BCP)")
                correo = st.text_input("Correo Corporativo")
                
                st.write("")
                espacio_izq, col_btn1, col_btn2, espacio_der = st.columns([0.5, 1.2, 1.2, 0.5])
                with col_btn1:
                    enviar = st.form_submit_button("Enviar PIN")
                with col_btn2:
                    volver = st.form_submit_button("Volver")
                
                if volver:
                    st.session_state.vista = "login"
                    st.rerun()
                if enviar:
                    correo_limpio = correo.strip().lower()
                    
                    if not correo_limpio:
                        st.error("Por favor, ingrese un correo electrónico.")
                    else:
                        import random
                        pin_generado = str(random.randint(100000, 999999))
                        
                        # 1. SI ES DOMINIO BCP (Acceso Automático)
                        if correo_limpio.endswith("@bcp.com.pe"):
                            st.session_state.temp_correo = correo_limpio
                            st.session_state.temp_pin = pin_generado
                            st.success(f"¡Código PIN generado con éxito! (Simulación de envío a {correo_limpio}: {pin_generado})")
                            # Aquí configuraremos en el siguiente paso el envío real por smtplib
                        
                        # 2. SI ES CORREO EXTERNO (Validación en Google Sheets)
                        else:
                            try:
                                # URL de exportación CSV de tu Google Sheet (Asegúrate de que la hoja sea pública para lectura)
                                sheet_url = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/export?format=csv&gid=0"
                                df_sheets = pd.read_csv(sheet_url)
                                
                                # Buscar si el correo existe en la columna 'Correo'
                                externos_permitidos = df_sheets['Correo'].str.strip().str.lower().tolist()
                                
                                if correo_limpio in externos_permitidos:
                                    st.session_state.temp_correo = correo_limpio
                                    st.session_state.temp_pin = pin_generado
                                    st.success(f"¡Excepción externa autorizada! PIN enviado: {pin_generado}")
                                else:
                                    st.error("Acceso denegado: Este correo no se encuentra autorizado.")
                            except Exception as e:
                                st.error("Error al conectar con la base de datos.")
                    
            st.markdown("<div class='footer-text'>© 2026 J&V RESGUARDO S.A.C.<br>Uso estrictamente gerencial y confidencial.</div>", unsafe_allow_html=True)

    # --- PANTALLA DE LOGIN ---
    elif st.session_state.vista == "login":
        col1, col2, col3 = st.columns([2.5, 1.4, 2.5]) 
        with col2:
            st.write("<br><br>", unsafe_allow_html=True) 
            st.markdown("<div class='top-label'>UNIDAD DE RESGUARDO EJECUTIVO</div>", unsafe_allow_html=True)
            st.markdown("<div class='main-title'>PORTAL DE CONTROL OPERATIVO</div>", unsafe_allow_html=True)
            st.markdown("<div class='sub-title'>Sistema Integrado de Gestión y Seguimiento</div>", unsafe_allow_html=True)
            
            with st.form("login_form"):
                st.markdown("<h5 style='text-align: center; margin-bottom: 25px; color: #002A8D;'>Credenciales de Acceso</h5>", unsafe_allow_html=True)
                
                usuario = st.text_input("Usuario Corporativo")
                password = st.text_input("Contraseña", type="password")
                
                st.write("") 
                
                espacio_izq, col_btn1, col_btn2, espacio_der = st.columns([0.5, 1.2, 1.2, 0.5])
                
                with col_btn1:
                    submit = st.form_submit_button("Ingresar")
                with col_btn2:
                    register = st.form_submit_button("Solicitar")
                
                if register:
                    st.session_state.vista = "registro"
                    st.rerun()
                    
                if submit:
                    if usuario == "admin" and password == "123":
                        st.session_state.logged_in = True
                        st.rerun()
                    else:
                        st.error("Acceso denegado. Contacte al administrador.")
                        
            st.markdown("<div class='footer-text'>© 2026 J&V RESGUARDO S.A.C.<br>Uso estrictamente gerencial y confidencial.</div>", unsafe_allow_html=True)

else:
    st.sidebar.markdown("<h3 style='text-align: center; color: #002A8D;'>Módulos de Gestión</h3>", unsafe_allow_html=True)
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
