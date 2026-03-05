import streamlit as st
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="App Corporativa Emiliano",
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

# 3. USUARIOS
USUARIOS = {
    "TAVERA": {"password": "Emiliano", "desde": "12/05/2025", "empresa": "Hotel1", "foto": "foto1.jpg", "caducidad": "20D"},
    "Julio": {"password": "estralla15", "desde": "08/01/2024", "empresa": "manufacturera", "foto": "foto2.jpg", "caducidad": "10D"},
    "Juan": {"password": "cantar72", "desde": "09/07/2025", "empresa": "hotel2", "foto": "foto3.jpg", "caducidad": "80D"},
    "Andres": {"password": "1234", "desde": "01/01/2026", "empresa": "fábrica juguetes", "foto": "foto4.jpg", "caducidad": "3D"}
}

# 4. FUNCIONES AUXILIARES
def crear_gauge(titulo, valor, color):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = valor,
        title = {'text': titulo, 'font': {'size': 24}},
        gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': color}}
    ))
    fig.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=20))
    return fig

def cerrar_sesion():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# 5. MAIN
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
        else:
            df_recursos_base = pd.DataFrame() 

        file_path_clima = 'smartsus_clima.csv'
        if os.path.exists(file_path_clima):
            df_clima_base = pd.read_csv(file_path_clima)
            df_clima_base['Date'] = pd.to_datetime(df_clima_base['Date'])
        else:
            df_clima_base = pd.DataFrame()

        # --- DASHBOARD ---
        if st.session_state.pagina_actual == "dashboard":
            # FILA 1: Medalla y Gauges
            f1_c1, f1_c2, f1_c3 = st.columns(3)
            with f1_c1:
                img_medal = "gold.jpeg" if st.session_state.user_name == "TAVERA" else ("plata.jpeg" if st.session_state.user_name == "Julio" else "bronce.jpeg")
                _, col_img, _ = st.columns([1, 2, 1])
                with col_img:
                    st.image(img_medal if os.path.exists(img_medal) else f"https://via.placeholder.com/150x150?text={img_medal}", use_container_width=True)
            with f1_c2: st.plotly_chart(crear_gauge("Eficiencia", 82, "#00CC96"), use_container_width=True)
            with f1_c3: st.plotly_chart(crear_gauge("Rendimiento", 55, "#636EFA"), use_container_width=True)

            # FILA 2: AGUA
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
                        df_a['Per'] = df_a['Date'] - pd.to_timedelta(df_a['Date'].dt.dayofweek, unit='d')
                        df_g = df_a.groupby('Per', as_index=False)['Liters'].sum()
                        df_g['Per'] = df_g['Per'].dt.strftime('%Y-%m-%d')
                        fig = px.line(df_g, x='Per', y='Liters', markers=True, title=f"Agua: {f_a_agua}", color_discrete_sequence=["#0077B6"])
                    else:
                        df_a['Fech'] = df_a['Date'].dt.strftime('%Y-%m-%d')
                        df_g = df_a.groupby('Fech', as_index=False)['Liters'].sum()
                        fig = px.line(df_g, x='Fech', y='Liters', markers=True, title=f"Agua: {f_a_agua}", color_discrete_sequence=["#0077B6"])
                    
                    fig.update_layout(xaxis_title="Fecha", yaxis_title="Litros", margin=dict(l=20, r=20, t=40, b=20), height=320)
                    st.plotly_chart(fig, use_container_width=True)

            # FILA 3: LUZ
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
                        df_l['Per'] = df_l['Date'] - pd.to_timedelta(df_l['Date'].dt.dayofweek, unit='d')
                        df_g = df_l.groupby('Per', as_index=False)['Electric Energy (kWh)'].sum()
                        df_g['Per'] = df_g['Per'].dt.strftime('%Y-%m-%d')
                        fig = px.line(df_g, x='Per', y='Electric Energy (kWh)', markers=True, title=f"Energía: {f_a_luz}", color_discrete_sequence=["#FFB703"])
                    else:
                        df_l['Fech'] = df_l['Date'].dt.strftime('%Y-%m-%d')
                        df_g = df_l.groupby('Fech', as_index=False)['Electric Energy (kWh)'].sum()
                        fig = px.line(df_g, x='Fech', y='Electric Energy (kWh)', markers=True, title=f"Energía: {f_a_luz}", color_discrete_sequence=["#FFB703"])
                    
                    fig.update_layout(xaxis_title="Fecha", yaxis_title="kWh", margin=dict(l=20, r=20, t=40, b=20), height=320)
                    st.plotly_chart(fig, use_container_width=True)
            with f3_c3:
                st.write("### Reporte Energía")
                st.dataframe(pd.DataFrame(np.random.randint(100,500,size=(5, 2)), columns=['Sector', 'kWh']), use_container_width=True)

            # FILA 4: CLIMA
            st.divider()
            f4_c1, f4_c23 = st.columns([1, 2])
            with f4_c1:
                st.write("### Sensores Ext.")
                st.dataframe(pd.DataFrame(np.random.randint(15,35,size=(5, 2)), columns=['Sensor', '°C']), use_container_width=True)
            with f4_c23:
                if not df_clima_base.empty:
                    col_filtros_clima = st.columns(1)[0] # Solo necesitamos un selector aquí
                    with col_filtros_clima:
                        filtro_tiempo_clima = st.selectbox("Promedio de Temperatura", ["Horario", "Diario", "Mensual"], key="clima_tiempo")

                    df_filtrado_clima = df_clima_base.copy()

                    # LÓGICA DE AGRUPACIÓN (MEAN en lugar de SUM)
                    if filtro_tiempo_clima == "Mensual":
                        # Agrupamos por Año-Mes y promediamos
                        df_filtrado_clima['Periodo'] = df_filtrado_clima['Date'].dt.strftime('%Y-%m')
                        df_agrupado_clima = df_filtrado_clima.groupby('Periodo', as_index=False)['Temperature (°C)'].mean()
                        x_col_clima = 'Periodo'
                    elif filtro_tiempo_clima == "Diario":
                        # Agrupamos por Día exacto y promediamos las 24 horas
                        df_filtrado_clima['Fecha'] = df_filtrado_clima['Date'].dt.strftime('%Y-%m-%d')
                        df_agrupado_clima = df_filtrado_clima.groupby('Fecha', as_index=False)['Temperature (°C)'].mean()
                        x_col_clima = 'Fecha'
                    else:
                        # Horario: Mostramos los 5000 registros tal cual
                        df_agrupado_clima = df_filtrado_clima
                        x_col_clima = 'Date'

                    # GRÁFICO PLOTLY - CLIMA
                    fig_clima = px.line(df_agrupado_clima, x=x_col_clima, y='Temperature (°C)', 
                                        markers=(filtro_tiempo_clima != "Horario"), # Quitamos los puntos si es por hora porque son demasiados
                                        title=f"Tendencia de Temperatura Costera ({filtro_tiempo_clima})", 
                                        color_discrete_sequence=["#2ECC71"])
                    
                    fig_clima.update_layout(xaxis_title="Tiempo", yaxis_title="Temperatura Promedio (°C)", 
                                            margin=dict(l=20, r=20, t=40, b=20), height=320)
                    st.plotly_chart(fig_clima, use_container_width=True)
                else:
                    st.warning("Archivo 'smartsus_clima.csv' no encontrado. Ejecuta el generador primero.")

        # OTRAS PÁGINAS (Entrenamiento, Usuario, Cuarta)... [Mismo código que antes]
        elif st.session_state.pagina_actual == "usuario":
            _, col_principal, _ = st.columns([0.15, 0.7, 0.15])
            with col_principal:
                st.markdown("<div class='perfil-titulo'>Perfil de Usuario</div>", unsafe_allow_html=True)
                col_img, col_txt = st.columns([0.5, 2.0])
                with col_img: st.image(user_info.get('foto', 'https://via.placeholder.com/200'), use_container_width=True)
                with col_txt:
                    st.markdown(f"<div class='perfil-dato'><b>Nombre:</b> {st.session_state.user_name}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='perfil-dato'><b>Empresa:</b> {user_info.get('empresa', '')}</div>", unsafe_allow_html=True)

        st.markdown("<br><br>", unsafe_allow_html=True)
        st.divider()
        if st.button("Cerrar sesión"): cerrar_sesion()

def mostrar_login():
    _, col_centro, _ = st.columns([1, 1, 1])
    with col_centro:
        st.title("Acceso al Sistema")
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("Acceder"):
            if u in USUARIOS and USUARIOS[u]["password"] == p:
                st.session_state.autenticado, st.session_state.user_name, st.session_state.pagina_actual = True, u, "dashboard"
                st.rerun()

if __name__ == "__main__":
    main()