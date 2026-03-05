import streamlit as st
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="SmartSUS - Dashboard Corporativo",
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# 2. ESTILOS CSS
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
    div.stButton > button:first-child {
        width: 100%;
        height: 3.5em;
        font-weight: bold;
    }
    .perfil-titulo { font-size: 3rem !important; font-weight: 700; text-align: center; margin-bottom: 30px; }
    .perfil-dato { font-size: 1.8rem !important; line-height: 1.6; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 3. BASE DE DATOS DE USUARIOS
USUARIOS = {
    "TAVERA": {"password": "Emiliano", "desde": "12/05/2025", "empresa": "Hotel1", "foto": "foto1.jpg", "caducidad": "20D"},
    "Julio": {"password": "estralla15", "desde": "08/01/2024", "empresa": "manufacturera", "foto": "foto2.jpg", "caducidad": "10D"},
    "Juan": {"password": "cantar72", "desde": "09/07/2025", "empresa": "hotel2", "foto": "foto3.jpg", "caducidad": "80D"},
    "Andres": {"password": "1234", "desde": "01/01/2026", "empresa": "fábrica juguetes", "foto": "foto4.jpg", "caducidad": "3D"}
}

# 4. FUNCIONES AUXILIARES
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
        # --- NAVEGACIÓN ---
        cols_nav = st.columns(4)
        secciones = ["Dashboard", "Entrenamiento", "Usuario", "Cuarta"]
        for i, seccion in enumerate(secciones):
            with cols_nav[i]:
                if st.button(seccion):
                    st.session_state.pagina_actual = seccion.lower()
                    st.rerun()
        st.divider()

        user_info = USUARIOS.get(st.session_state.user_name, {})
        
        # --- CARGA DE DATOS ---
        file_path_recursos = 'smartsus_simulated_resources.csv'
        if os.path.exists(file_path_recursos):
            df_recursos_base = pd.read_csv(file_path_recursos)
            df_recursos_base['Date'] = pd.to_datetime(df_recursos_base['Date'])
            total_agua = df_recursos_base['Liters'].sum()
            total_luz = df_recursos_base['Electric Energy (kWh)'].sum()
        else:
            df_recursos_base = pd.DataFrame()
            total_agua, total_luz = 0, 0

        file_path_clima = 'smartsus_clima.csv'
        if os.path.exists(file_path_clima):
            df_clima_base = pd.read_csv(file_path_clima)
            df_clima_base['Date'] = pd.to_datetime(df_clima_base['Date'])
        else:
            df_clima_base = pd.DataFrame()

        # --- CONTENIDO DE PÁGINAS ---

        if st.session_state.pagina_actual == "dashboard":
            
            # CONFIGURACIÓN DE TARGETS
            with st.expander("🎯 Configurar Objetivos Anuales (Targets)"):
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    t_agua = st.number_input("Meta de Agua (L)", min_value=1.0, value=max(float(total_agua)*1.2, 100.0))
                with col_t2:
                    t_luz = st.number_input("Meta de Energía (kWh)", min_value=1.0, value=max(float(total_luz)*1.2, 500.0))

            # FILA 1: Medalla y Gauges
            f1_c1, f1_c2, f1_c3 = st.columns(3)
            with f1_c1:
                img_medal = "gold.jpeg" if st.session_state.user_name == "TAVERA" else ("plata.jpeg" if st.session_state.user_name == "Julio" else "bronce.jpeg")
                _, col_img, _ = st.columns([1, 2, 1])
                with col_img:
                    st.image(img_medal if os.path.exists(img_medal) else f"https://via.placeholder.com/150x150?text={img_medal}", use_container_width=True)
            
            with f1_c2:
                fig_agua = go.Figure(go.Indicator(
                    mode = "gauge+number+delta", value = total_agua,
                    delta = {'reference': t_agua, 'increasing': {'color': "red"}, 'decreasing': {'color': "green"}},
                    title = {'text': "Consumo Acumulado Agua (L)", 'font': {'size': 20}},
                    gauge = {'axis': {'range': [0, t_agua]}, 'bar': {'color': "#0077B6"},
                             'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': t_agua}}
                ))
                fig_agua.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=20))
                st.plotly_chart(fig_agua, use_container_width=True)

            with f1_c3:
                fig_luz = go.Figure(go.Indicator(
                    mode = "gauge+number+delta", value = total_luz,
                    delta = {'reference': t_luz, 'increasing': {'color': "red"}, 'decreasing': {'color': "green"}},
                    title = {'text': "Consumo Acumulado Energía (kWh)", 'font': {'size': 20}},
                    gauge = {'axis': {'range': [0, t_luz]}, 'bar': {'color': "#FFB703"},
                             'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': t_luz}}
                ))
                fig_luz.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=20))
                st.plotly_chart(fig_luz, use_container_width=True)

            # FILA 2: TABLA Y GRÁFICA AGUA
            st.divider()
            f2_c1, f2_c23 = st.columns([1, 2])
            with f2_c1:
                st.write("### Consumo Diario")
                st.dataframe(pd.DataFrame(np.random.randint(10,50,size=(5, 2)), columns=['Lote', 'm3']), use_container_width=True)
            with f2_c23:
                if not df_recursos_base.empty:
                    c1, c2 = st.columns(2)
                    with c1: f_t_agua = st.selectbox("Temporalidad (Agua)", ["Diario", "Semanal"], key="a_t")
                    with c2: 
                        areas = ["Todas las áreas"] + list(df_recursos_base['Department'].unique())
                        f_a_agua = st.selectbox("Departamento (Agua)", areas, key="a_a")
                    
                    df_a = df_recursos_base.copy()
                    if f_a_agua != "Todas las áreas": df_a = df_a[df_a['Department'] == f_a_agua]
                    
                    if f_t_agua == "Semanal":
                        df_g = df_a.groupby(pd.Grouper(key='Date', freq='W-MON'))['Liters'].sum().reset_index()
                    else:
                        df_g = df_a.groupby(df_a['Date'].dt.date)['Liters'].sum().reset_index()
                    
                    df_g.columns = ['Date', 'Liters']
                    fig = px.line(df_g, x='Date', y='Liters', markers=True, title=f"Histórico Agua: {f_a_agua}", color_discrete_sequence=["#0077B6"])
                    st.plotly_chart(fig, use_container_width=True)

            # FILA 3: GRÁFICA LUZ Y TABLA
            st.divider()
            f3_c12, f3_c3 = st.columns([2, 1])
            with f3_c12:
                if not df_recursos_base.empty:
                    c1, c2 = st.columns(2)
                    with c1: f_t_luz = st.selectbox("Temporalidad (Energía)", ["Diario", "Semanal"], key="l_t")
                    with c2: f_a_luz = st.selectbox("Departamento (Energía)", areas, key="l_a")
                    
                    df_l = df_recursos_base.copy()
                    if f_a_luz != "Todas las áreas": df_l = df_l[df_l['Department'] == f_a_luz]
                    
                    if f_t_luz == "Semanal":
                        df_gl = df_l.groupby(pd.Grouper(key='Date', freq='W-MON'))['Electric Energy (kWh)'].sum().reset_index()
                    else:
                        df_gl = df_l.groupby(df_l['Date'].dt.date)['Electric Energy (kWh)'].sum().reset_index()
                    
                    df_gl.columns = ['Date', 'Electric Energy (kWh)']
                    fig_l = px.line(df_gl, x='Date', y='Electric Energy (kWh)', markers=True, title=f"Histórico Energía: {f_a_luz}", color_discrete_sequence=["#FFB703"])
                    st.plotly_chart(fig_l, use_container_width=True)
            with f3_c3:
                st.write("### Reporte Energía")
                st.dataframe(pd.DataFrame(np.random.randint(100,500,size=(5, 2)), columns=['Sector', 'kWh']), use_container_width=True)

            # FILA 4: TABLA Y GRÁFICA CLIMA
            st.divider()
            f4_c1, f4_c23 = st.columns([1, 2])
            with f4_c1:
                st.write("### Sensores Ext.")
                st.dataframe(pd.DataFrame(np.random.randint(15,35,size=(5, 2)), columns=['Sensor', '°C']), use_container_width=True)
            with f4_c23:
                if not df_clima_base.empty:
                    f_clima = st.selectbox("Promedio Temperatura", ["Horario", "Diario", "Mensual"], key="clima_t")
                    
                    df_c = df_clima_base.copy()
                    if f_clima == "Mensual":
                        # Cambio de 'ME' a 'MS' para mayor compatibilidad
                        df_cg = df_c.groupby(pd.Grouper(key='Date', freq='MS'))['Temperature (°C)'].mean().reset_index()
                    elif f_clima == "Diario":
                        df_cg = df_c.groupby(df_c['Date'].dt.date)['Temperature (°C)'].mean().reset_index()
                    else:
                        df_cg = df_c
                    
                    # Aseguramos que la columna de fecha se llame 'Date' antes de graficar
                    df_cg.rename(columns={df_cg.columns[0]: 'Date'}, inplace=True)
                    
                    fig_c = px.line(df_cg, x='Date', y='Temperature (°C)', title=f"Tendencia Clima ({f_clima})", color_discrete_sequence=["#2ECC71"])
                    st.plotly_chart(fig_c, use_container_width=True)

        elif st.session_state.pagina_actual == "entrenamiento":
            st.title("Centro de Datos y Entrenamiento")
            st.info("Sube nuevos archivos para actualizar el Dashboard")
            u1, u2 = st.columns(2)
            with u1: st.file_uploader("Actualizar Recursos (CSV)", type="csv")
            with u2: st.file_uploader("Actualizar Clima (CSV)", type="csv")

        elif st.session_state.pagina_actual == "usuario":
            _, col_p, _ = st.columns([0.15, 0.7, 0.15])
            with col_p:
                st.markdown("<div class='perfil-titulo'>Perfil de Usuario</div>", unsafe_allow_html=True)
                c_img, c_txt = st.columns([0.5, 2.0])
                with c_img: st.image(user_info.get('foto', 'https://via.placeholder.com/200'), use_container_width=True)
                with c_txt:
                    st.markdown(f"<div class='perfil-dato'><b>Nombre:</b> {st.session_state.user_name}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='perfil-dato'><b>Empresa:</b> {user_info.get('empresa', '')}</div>", unsafe_allow_html=True)

        st.markdown("<br><br>", unsafe_allow_html=True); st.divider()
        if st.button("Cerrar sesión"): cerrar_sesion()

def mostrar_login():
    _, col_c, _ = st.columns([1, 1, 1])
    with col_c:
        st.title("Acceso al Sistema")
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("Acceder"):
            if u in USUARIOS and USUARIOS[u]["password"] == p:
                st.session_state.autenticado, st.session_state.user_name, st.session_state.pagina_actual = True, u, "dashboard"
                st.rerun()

if __name__ == "__main__":
    main()

if __name__ == "__main__":

    main()
