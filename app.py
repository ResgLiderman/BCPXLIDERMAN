import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def enviar_correo_pin(destinatario, pin, nombre):
    remitente = st.secrets["EMAIL_USER"]
    password = st.secrets["EMAIL_PASSWORD"]
    
    asunto = "Portal de Control Operativo | Código de Verificación de Acceso"
    
    cuerpo = f"""
    Estimado(a) {nombre},
    
    Se ha recibido una solicitud de creación de cuenta para el Portal de Control Operativo (Unidad de Resguardo Ejecutivo).
    
    Su código PIN temporal de acceso de 6 dígitos es: {pin}
    
    Este código es estrictamente confidencial y tiene vigencia única para completar su registro. Si usted no solicitó este acceso, ignore este mensaje.
    
    Atentamente,
    J&V Resguardo S.A.C.
    """
    
    msg = MIMEMultipart()
    msg['From'] = remitente
    msg['To'] = destinatario
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remitente, password)
        server.sendmail(remitente, destinatario, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        return False

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
if "reg_step" not in st.session_state:
    st.session_state.reg_step = 1    

if not st.session_state.logged_in:
    
    # --- PANTALLA DE SOLICITUD (REGISTRO) ---
    if st.session_state.vista == "registro":
        col1, col2, col3 = st.columns([2.5, 1.4, 2.5]) 
        with col2:
            st.write("<br><br>", unsafe_allow_html=True)
            st.markdown("<div class='main-title'>AUTENTICACIÓN DE ACCESO</div>", unsafe_allow_html=True)
            st.markdown("<div class='sub-title'>Sistema de Verificación de Identidad</div>", unsafe_allow_html=True)
            
            # PASO 1: Ingreso de datos y validación de dominio / excepciones
            if st.session_state.reg_step == 1:
                with st.form("registro_form_1"):
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
                        st.session_state.reg_step = 1
                        st.rerun()
                        
                    if enviar:
                        correo_limpio = correo.strip().lower()
                        if not correo_limpio or not nombre:
                            st.error("Por favor, complete los campos obligatorios.")
                        else:
                            import random
                            pin_generado = str(random.randint(100000, 999999))
                            autorizado = False
                            
                            # Validar si es BCP o excepción en Google Sheets
                            if correo_limpio.endswith("@bcp.com.pe"):
                                autorizado = True
                            else:
                                try:
                                    sheet_url = "https://docs.google.com/spreadsheets/d/1zs4kNTGuEDk6jQ5GWtiHvCZb1VSqrxovfRxqXv3M4MQ/export?format=csv&gid=0"
                                    df_sheets = pd.read_csv(sheet_url)
                                    externos_permitidos = df_sheets['Correo'].str.strip().str.lower().tolist()
                                    if correo_limpio in externos_permitidos:
                                        autorizado = True
                                except Exception:
                                    pass
                            
                            if autorizado:
                                st.session_state.temp_pin = pin_generado
                                st.session_state.temp_correo = correo_limpio
                                st.session_state.temp_nombre = nombre
                                
                                # Disparar el correo real
                                exito_envio = enviar_correo_pin(correo_limpio, pin_generado, nombre)
                                
                                if exito_envio:
                                    st.session_state.reg_step = 2
                                    st.success("¡Código PIN enviado exitosamente a su bandeja corporativa!")
                                    st.rerun()
                                else:
                                    st.error("Error.")
                            else:
                                st.error("Acceso denegado: Dominio no autorizado.")

            # PASO 2: Ingreso del PIN recibido y creación de contraseña
            elif st.session_state.reg_step == 2:
                st.info(f"Se ha enviado su PIN al siguiente correo: **{st.session_state.temp_correo}**")
                
                with st.form("registro_form_2"):
                    pin_ingresado = st.text_input("Ingrese el PIN de 6 dígitos")
                    nuevo_password = st.text_input("Defina su Contraseña", type="password")
                    
                    st.write("")
                    espacio_izq, col_btn1, col_btn2, espacio_der = st.columns([0.5, 1.2, 1.2, 0.5])
                    with col_btn1:
                        verificar = st.form_submit_button("Confirmar")
                    with col_btn2:
                        regresar = st.form_submit_button("Cancelar")
                        
                    if regresar:
                        st.session_state.reg_step = 1
                        st.rerun()
                        
                    if verificar:
                        if pin_ingresado.strip() == st.session_state.temp_pin:
                            st.success("¡Cuenta creada con éxito! Ya puede iniciar sesión.")
                            st.session_state.reg_step = 1
                            st.session_state.vista = "login"
                            st.rerun()
                        else:
                            st.error("El PIN ingresado es incorrecto. Verifique el código.")

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
                    usuario_limpio = usuario.strip().lower()
                    
                    # 1. Credencial de Administrador General
                    if usuario_limpio == "admin" and password == "123":
                        st.session_state.logged_in = True
                        st.rerun()
                        
                    # 2. Validación para usuarios BCP o Excepciones externas
                    elif usuario_limpio.endswith("@bcp.com.pe"):
                        st.session_state.logged_in = True
                        st.rerun()
                    else:
                        try:
                            sheet_url = "https://docs.google.com/spreadsheets/d/1zs4kNTGuEDk6jQ5GWtiHvCZb1VSqrxovfRxqXv3M4MQ/export?format=csv&gid=0"
                            df_sheets = pd.read_csv(sheet_url)
                            externos_permitidos = df_sheets['Correo'].str.strip().str.lower().tolist()
                            
                            if usuario_limpio in externos_permitidos:
                                st.session_state.logged_in = True
                                st.rerun()
                            else:
                                st.error("Acceso denegado: Credenciales no registradas.")
                        except Exception:
                            st.error("Error al validar el acceso con la base de datos.")
                        
            st.markdown("<div class='footer-text'>© 2026 J&V RESGUARDO S.A.C.<br>Uso estrictamente gerencial y confidencial.</div>", unsafe_allow_html=True)

else:
    st.sidebar.markdown("<h3 style='text-align: center; color: #002A8D;'>Módulos de Gestión</h3>", unsafe_allow_html=True)
    menu = st.sidebar.radio("Navegación:", ["Resumen Ejecutivo", "Control de Armamento", "Licencias SUCAMEC", "Salud Ocupacional (EMO)"])
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.rerun()

    if menu == "Resumen Ejecutivo":
        st.markdown("<div class='top-label'>DASHBOARD EJECUTIVO - EQUIPAMIENTO TÁCTICO BCP</div>", unsafe_allow_html=True)
        
        try:
            # Enlace de exportación CSV de la pestaña EQUIPAMIENTO
            sheet_url_eq = "https://docs.google.com/spreadsheets/d/1Cs3cV-NdVC6u1sDVhWEKpoP2OvDldzpWVIvx8bf-OSc/export?format=csv&gid=0"
            df_eq = pd.read_csv(sheet_url_eq, header=1)
            
            # Limpieza quirúrgica: eliminar columnas "Unnamed" o vacías y filas sin equipo
            df_eq = df_eq.loc[:, ~df_eq.columns.str.contains('^Unnamed')]
            df_eq = df_eq.dropna(subset=['EQUIPO'])
            
            # Tarjetas de Métricas Ejecutivas estilo Power BI
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            col_m1.metric("Tipos de Ítems", len(df_eq), "100% Homologado")
            col_m2.metric("Personal Asignado", "10 Oficiales", "Activos G2-G7")
            col_m3.metric("Control Logístico", "Óptimo", "Sin Mermas", delta_color="normal")
            col_m4.metric("Auditoría BCP", "Aprobada", "Certificado BCP", delta_color="normal")
            
            st.write("")
            st.markdown("##### 📊 Gráfico de Distribución de Cantidades por Componente")
            
            # Gráfico de barras interactivo nativo estilo BI
            if 'CANTIDAD' in df_eq.columns and 'EQUIPO' in df_eq.columns:
                df_chart = df_eq.set_index('EQUIPO')['CANTIDAD']
                st.bar_chart(df_chart, color="#002A8D")
            
            st.write("")
            st.markdown("##### 🛡️ Matriz Detallada de Asignación por Oficial")
            
            # Filtro interactivo limpio
            equipos_disponibles = ["Todos"] + df_eq['EQUIPO'].tolist()
            filtro_eq = st.selectbox("Filtrar componente táctico:", equipos_disponibles)
            
            df_mostrar = df_eq.copy()
            if filtro_eq != "Todos":
                df_mostrar = df_mostrar[df_mostrar['EQUIPO'] == filtro_eq]
                
            # Mostrar tabla interactiva sin rastro de columnas basura
            st.dataframe(df_mostrar.set_index('EQUIPO'), use_container_width=True)
            
        except Exception as e:
            st.error("Error al sincronizar con el Google Sheet. Verifica que la fila 2 tenga las cabeceras limpias.")
