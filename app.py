import streamlit as st
import pandas as pd

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Portal Ejecutivo | BCP - Liderman", layout="wide")

# 2. CSS CORPORATIVO Y EFECTO 3D (Glass/Card Effect)
st.markdown("""
    <style>
        /* Contenedor principal del Login (Efecto Tarjeta flotante 3D) */
        [data-testid="stForm"] {
            background: linear-gradient(145deg, #1e2228, #191c21); /* Fondo oscuro elegante */
            border: 1px solid #2c323a;
            border-radius: 12px;
            padding: 40px 30px;
            box-shadow: 0px 20px 40px rgba(0, 0, 0, 0.7), 
                        0px 5px 15px rgba(0, 0, 0, 0.5); /* Sombra 3D profunda */
        }
        
        /* Tipografía general */
        h1, h2, h3, h4 {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
        }
        
        /* Modificar el botón de ingreso */
        div.stButton > button:first-child {
            background-color: #002A8D !important; /* Azul BCP */
            color: white !important;
            border-radius: 6px;
            border: none;
            width: 100%; /* Botón de ancho completo */
            font-size: 16px;
            font-weight: 600;
            padding: 0.6rem;
            margin-top: 20px;
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3); /* Sombra 3D al botón */
            transition: all 0.3s ease;
        }
        div.stButton > button:first-child:hover {
            background-color: #001f6b !important;
            transform: translateY(-2px); /* Efecto de levitación al pasar el mouse */
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.5);
        }
        
        /* Barra superior falsa BCP */
        .top-bar {
            background-color: #002A8D;
            padding: 12px;
            border-radius: 4px;
            color: white;
            text-align: center;
            font-weight: 600;
            font-size: 13px;
            letter-spacing: 1.5px;
            margin-bottom: 40px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
        }
        
        /* Textos estilizados */
        .sub-title {
            text-align: center; 
            color: #A0AAB5; 
            font-size: 15px;
            margin-top: -15px;
            margin-bottom: 40px;
        }
        .footer-text {
            text-align: center; 
            color: #5b6571; 
            font-size: 12px;
            margin-top: 50px;
            line-height: 1.5;
        }
    </style>
""", unsafe_allow_html=True)

# 3. CONTROL DE SESIÓN
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- PANTALLA DE LOGIN ---
if not st.session_state.logged_in:
    # Ajustamos las columnas para que la caja quede más centrada y proporcionada
    col1, col2, col3 = st.columns([1.5, 2, 1.5]) 
    
    with col2:
        st.markdown("<div class='top-bar'>PORTAL DE SEGURIDAD EJECUTIVA | CREDICORP</div>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; color: #ffffff; letter-spacing: 2px;'>LIDERMAN <span style='color:#FF7800;'>x</span> BCP</h1>", unsafe_allow_html=True)
        st.markdown("<p class='sub-title'>Sistema de Gestión y Seguimiento Operativo Diario</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.markdown("<h4 style='text-align: center; margin-bottom: 25px; color: #ffffff;'>Autenticación de Usuario</h4>", unsafe_allow_html=True)
            
            # Cajas limpias, sin emojis ni pistas
            usuario = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            
            submit = st.form_submit_button("Ingresar al Sistema")
            
            if submit:
                # Internamente la clave sigue siendo la misma, pero ya no se muestra en pantalla
                if usuario == "admin" and password == "123":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas. Verifique sus accesos.")
                    
        st.markdown("<p class='footer-text'>© 2026 Banco de Crédito del Perú | J&V Resguardo S.A.C.<br>Información de carácter estrictamente confidencial.</p>", unsafe_allow_html=True)

# --- PANEL PRINCIPAL (DASHBOARD) ---
else:
    st.sidebar.markdown("<h3 style='text-align: center; color: #002A8D;'>Módulos BCP</h3>", unsafe_allow_html=True)
    st.sidebar.write("---")
    menu = st.sidebar.radio(
        "Navegación Operativa:",
        ["Resumen Ejecutivo", "Control de Armamento", "Licencias SUCAMEC", "Salud Ocupacional (EMO)", "Configuración"]
    )
    
    st.sidebar.write("---")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.rerun()

    if menu == "Resumen Ejecutivo":
        st.markdown("<div class='top-bar'>DASHBOARD GENERAL DE OPERACIONES - SETIEMBRE 2026</div>", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric(label="Personal Activo", value="9", delta="Escolta y G2-G7")
        with col2: st.metric(label="Armamento Completo", value="100%", delta="Verificado")
        with col3: st.metric(label="Cumplimiento PAC", value="89%", delta="-1 Pendiente", delta_color="inverse")
        with col4: st.metric(label="EMOs Vigentes", value="77.8%", delta="1 Observado", delta_color="inverse")
        
        st.write("---")
        st.subheader("Alertas del Sistema")
        st.warning("Observación Médica: Víctor Resurrección Morales - Pendiente interconsulta oftalmológica.")
        st.info("Renovación SUCAMEC: Manuel Saavedra Maurtua - Licencia por vencer en Feb 2027.")

    elif menu == "Control de Armamento":
        st.markdown("<div class='top-bar'>INVENTARIO FÍSICO DE ARMAMENTO Y EQUIPOS</div>", unsafe_allow_html=True)
        st.write("Auditoría de asignación de equipos críticos para el servicio de resguardo.")
        
        data = {
            "Agente": ["Víctor Resurrección", "Jorge Bonilla", "Wismer Farfán", "Miguel Calle"],
            "Puesto": ["G2", "G2", "G4", "G4"],
            "Glock": ["OK", "OK", "OK", "OK"],
            "Munición": ["30", "30", "30", "30"],
            "Chaleco": ["OK", "OK", "OK", "OK"],
            "Funda Chaleco": ["OK", "FALTA", "OK", "OK"]
        }
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)

    else:
        st.title(menu)
        st.write("Módulo en construcción para conexión con base de datos.")
