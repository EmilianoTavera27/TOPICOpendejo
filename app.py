import streamlit as st
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. CONFIGURACIÓN DE PÁGINA (MODO WEB WIDE)
st.set_page_config(
    page_title="App Corporativa Emiliano",
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# 2. ESTILOS CSS PERSONALIZADOS
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100%;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Botones de navegación uniformes */
    div.stButton > button:first-child {
        width: 100%;
        height: 3.5em;
        font-weight: bold;
    }

    /* Estilos para la sección de Perfil */
    .perfil-titulo {
        font-size: 3rem !important;
        font-weight: 700;
        text-align: center;
        margin-bottom: 30px;
    }
    .perfil-dato {
        font-size: 1.8rem !important;
        line-height: 1.6;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. BASE DE DATOS DE USUARIOS
USUARIOS = {
    "TAVERA": {"password": "Emiliano", "desde": "12/05/2025", "empresa": "Hotel1", "foto": "foto1.jpg", "caducidad": "20D"},
    "Julio": {"password": "estralla15", "desde": "08/01/2024", "empresa": "manufacturera", "foto": "foto2.jpg", "caducidad": "10D"},
    "Juan": {"password": "cantar72", "desde": "09/07/2025", "empresa": "hotel2", "foto": "foto3.jpg", "caducidad": "80D"},
    "Andres": {"password": "1234", "desde": "01/01/2026", "empresa": "fábrica juguetes", "foto": "foto4.jpg", "caducidad": "3D"},
    "Erick": {"password": "1234", "desde": "02/01/2025", "empresa": "fábrica equipo médico", "foto": "foto5.jpg", "caducidad": "14D"}
}

# 4. FUNCIONES AUXILIARES PARA GRÁFICOS
def crear_gauge(titulo, valor, color):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = valor,
        title = {'text': titulo, 'font': {'size': 24}},
        gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': color}}
    ))
    fig.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=20))
    return fig

def crear_serie_tiempo(titulo, color):
    chart_data = pd.DataFrame(np.random.randn(20, 1), columns=[titulo])
    st.subheader(titulo)
    st.line_chart(chart_data, color=color)

def cerrar_sesion():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# 5. LÓGICA PRINCIPAL
def main():
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False
    if 'pagina_actual' not in st.session_state:
        st.session_state.pagina_actual = "dashboard"

    if not st.session_state.autenticado:
        mostrar_login()
    else:
        # --- NAVEGACIÓN SUPERIOR ---
        cols_nav = st.columns(4)
        secciones = ["Dashboard", "Entrenamiento", "Usuario", "Cuarta"]
        for i, seccion in enumerate(secciones):
            with cols_nav[i]:
                if st.button(seccion):
                    st.session_state.pagina_actual = seccion.lower()
                    st.rerun()
        st.divider()

        user_info = USUARIOS[st.session_state.user_name]

        # --- CONTENIDO DE PÁGINAS ---
        
        # A. DASHBOARD (MATRIZ 4x3)
        if st.session_state.pagina_actual == "dashboard":
            # FILA 1: Imagen condicional y Gauges
            f1_c1, f1_c2, f1_c3 = st.columns(3)
            with f1_c1:
                # Lógica de medallas
                if st.session_state.user_name == "TAVERA":
                    img_medal = "gold.jpeg"
                elif st.session_state.user_name == "Julio":
                    img_medal = "plata.jpeg"
                else:
                    img_medal = "bronce.jpeg"
                
                if os.path.exists(img_medal):
                    st.image(img_medal, use_container_width=True)
                else:
                    st.image(f"https://via.placeholder.com/300x200?text={img_medal}", use_container_width=True)
            
            with f1_c2:
                st.plotly_chart(crear_gauge("Eficiencia", 82, "#00CC96"), use_container_width=True)
            with f1_c3:
                st.plotly_chart(crear_gauge("Rendimiento", 55, "#636EFA"), use_container_width=True)

            # FILA 2: Tabla y Serie AGUA (combinada)
            f2_c1, f2_c23 = st.columns([1, 2])
            with f2_c1:
                st.write("### Consumo Diario")
                st.dataframe(pd.DataFrame(np.random.randint(10,50,size=(5, 2)), columns=['Lote', 'm3']), use_container_width=True)
            with f2_c23:
                crear_serie_tiempo("AGUA", "#0077B6")

            # FILA 3: Serie LUZ (combinada) y Tabla
            f3_c12, f3_c3 = st.columns([2, 1])
            with f3_c12:
                crear_serie_tiempo("LUZ", "#FFB703")
            with f3_c3:
                st.write("### Reporte Energía")
                st.dataframe(pd.DataFrame(np.random.randint(100,500,size=(5, 2)), columns=['Sector', 'kWh']), use_container_width=True)

            # FILA 4: Tabla y Serie CLIMA (combinada)
            f4_c1, f4_c23 = st.columns([1, 2])
            with f4_c1:
                st.write("### Sensores Ext.")
                st.dataframe(pd.DataFrame(np.random.randint(15,35,size=(5, 2)), columns=['Sensor', '°C']), use_container_width=True)
            with f4_c23:
                crear_serie_tiempo("CLIMA", "#2ECC71")

        # B. ENTRENAMIENTO
        elif st.session_state.pagina_actual == "entrenamiento":
            st.title("Sección de Entrenamiento")
            st.write("Espacio para carga de modelos y datasets.")

        # C. USUARIO (PERFIL CENTRADO)
        elif st.session_state.pagina_actual == "usuario":
            _, col_principal, _ = st.columns([0.15, 0.7, 0.15])
            with col_principal:
                st.markdown("<div class='perfil-titulo'>Perfil de Usuario</div>", unsafe_allow_html=True)
                # Proporción de foto 1/3 (0.5 a 2.0)
                col_img, col_txt = st.columns([0.5, 2.0])
                with col_img:
                    ruta_foto = user_info['foto']
                    if os.path.exists(ruta_foto):
                        st.image(ruta_foto, use_container_width=True)
                    else:
                        st.image("https://via.placeholder.com/200", use_container_width=True)
                with col_txt:
                    st.markdown(f"<div class='perfil-dato'><b>Nombre:</b> {st.session_state.user_name}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='perfil-dato'><b>Empresa:</b> {user_info['empresa']}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='perfil-dato'><b>Miembro desde:</b> {user_info['desde']}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='perfil-dato'><b>Suscripción:</b> {user_info['caducidad']} restantes</div>", unsafe_allow_html=True)

        # D. CUARTA PÁGINA
        elif st.session_state.pagina_actual == "cuarta":
            st.title("Configuración del Sistema")
            st.write("Parámetros adicionales de la aplicación.")

        # --- PIE DE PÁGINA ---
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.divider()
        if st.button("Cerrar sesión"):
            cerrar_sesion()

def mostrar_login():
    _, col_centro, _ = st.columns([1, 1, 1])
    with col_centro:
        st.title("Acceso al Sistema")
        u = st.text_input("Nombre de Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("Acceder"):
            if u in USUARIOS and USUARIOS[u]["password"] == p:
                st.session_state.autenticado = True
                st.session_state.user_name = u
                st.session_state.pagina_actual = "dashboard"
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")

if __name__ == "__main__":
    main()