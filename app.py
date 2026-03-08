import streamlit as st
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import datetime # NUEVO: Para manejar los días de mañana y pasado

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

# NUEVO: Función Predictiva Ágil (Regresión Lineal Simple)
def generar_prediccion(df, col_fecha, col_valor, operacion='sum'):
    if df.empty or col_fecha not in df.columns or col_valor not in df.columns:
        return pd.DataFrame({"Día": ["Mañana", "Pasado mañana"], "Predicción Uso": [0.0, 0.0]})
    
    # Preparamos datos por día
    df_temp = df.copy()
    df_temp[col_fecha] = pd.to_datetime(df_temp[col_fecha]).dt.date
    
    if operacion == 'sum':
        df_grp = df_temp.groupby(col_fecha)[col_valor].sum().reset_index()
    else:
        df_grp = df_temp.groupby(col_fecha)[col_valor].mean().reset_index()
        
    df_grp = df_grp.sort_values(col_fecha).dropna(subset=[col_valor])
    
    if len(df_grp) < 2: # Fallback si hay pocos datos
        val = df_grp[col_valor].iloc[0] if len(df_grp) == 1 else 0.0
        return pd.DataFrame({"Día": ["Mañana", "Pasado mañana"], "Predicción Uso": [round(val, 1), round(val, 1)]})

    # Usamos los últimos 14 días para capturar la tendencia actual sin ruido viejo
    df_grp = df_grp.tail(14)
    
    x = np.arange(len(df_grp))
    y = df_grp[col_valor].values
    
    if np.all(y == y[0]):
        p1, p2 = y[0], y[0]
    else:
        # Matemática: Ajuste lineal de mínimos cuadrados
        z = np.polyfit(x, y, 1) 
        p = np.poly1d(z)
        p1 = p(len(df_grp))     # Predicción día +1
        p2 = p(len(df_grp) + 1) # Predicción día +2
        
    ultimo_dia = df_grp[col_fecha].iloc[-1]
    dia1 = ultimo_dia + datetime.timedelta(days=1)
    dia2 = ultimo_dia + datetime.timedelta(days=2)
    
    return pd.DataFrame({
        "Día": [f"24Hrs ({dia1.strftime('%d/%m')})", f"48Hrs ({dia2.strftime('%d/%m')})"],
        "Predicción Uso": [max(0, round(p1, 1)), max(0, round(p2, 1))] # Evitamos predecir consumos negativos
    })

# 5. LÓGICA PRINCIPAL
def main():
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False
    if 'pagina_actual' not in st.session_state:
        st.session_state.pagina_actual = "dashboard"
    if 'df_limpieza_sesion' not in st.session_state:
        st.session_state.df_limpieza_sesion = pd.DataFrame()
    if 'df_otro_sesion' not in st.session_state:
        st.session_state.df_otro_sesion = pd.DataFrame()
    
    if 't_agua_val' not in st.session_state:
        st.session_state.t_agua_val = 50000000.0  
    if 't_luz_val' not in st.session_state:
        st.session_state.t_luz_val = 50000000.0   

    if not st.session_state.autenticado:
        mostrar_login()
    else:
        # --- NAVEGACIÓN ---
        cols_nav = st.columns(4)
        secciones = ["Dashboard", "Entrenamiento", "Usuario", "Cuarta"]
        for i, seccion in enumerate(secciones):
            with cols_nav[i]:
                if st.button(seccion, key=f"nav_btn_{seccion}_{i}"):
                    st.session_state.pagina_actual = seccion.lower()
                    st.rerun()
        st.divider()

        user_info = USUARIOS.get(st.session_state.user_name, {})
        
        # --- CARGA DE DATOS ---
        file_path_recursos = 'smartsus_simulated_resources.csv'
        if os.path.exists(file_path_recursos):
            df_recursos_base = pd.read_csv(file_path_recursos)
            df_recursos_base['Date'] = pd.to_datetime(df_recursos_base['Date'])
            total_agua_base = df_recursos_base['Liters'].sum()
            total_luz_base = df_recursos_base['Electric Energy (kWh)'].sum()
        else:
            df_recursos_base = pd.DataFrame()
            total_agua_base, total_luz_base = 0, 0

        total_agua_limp = st.session_state.df_limpieza_sesion['Water Consumed (Liters)'].sum() if not st.session_state.df_limpieza_sesion.empty else 0
        total_agua_equi = st.session_state.df_otro_sesion['Water Consumed (Liters)'].sum() if not st.session_state.df_otro_sesion.empty else 0
        total_luz_equi = st.session_state.df_otro_sesion['Energy Consumed (kWh)'].sum() if not st.session_state.df_otro_sesion.empty else 0

        total_agua_total = total_agua_base + total_agua_limp + total_agua_equi
        total_luz_total = total_luz_base + total_luz_equi

        pct_agua = (total_agua_total / st.session_state.t_agua_val) * 100 if st.session_state.t_agua_val > 0 else 0
        pct_luz = (total_luz_total / st.session_state.t_luz_val) * 100 if st.session_state.t_luz_val > 0 else 0

        # A. DASHBOARD
        if st.session_state.pagina_actual == "dashboard":
            
            with st.expander("🎯 Configurar Objetivos Anuales (Targets)"):
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    st.session_state.t_agua_val = st.number_input("Meta Agua (L)", value=st.session_state.t_agua_val, step=100.0)
                with col_t2:
                    st.session_state.t_luz_val = st.number_input("Meta Energía (kWh)", value=st.session_state.t_luz_val, step=50.0)

            # FILA 1: Medalla y Gauges
            f1_c1, f1_c2, f1_c3 = st.columns(3)
            with f1_c1:
                img_medal = "gold.jpeg" if st.session_state.user_name == "TAVERA" else ("plata.jpeg" if st.session_state.user_name == "Julio" else "bronce.jpeg")
                _, col_img, _ = st.columns([1, 2, 1])
                with col_img: st.image(img_medal if os.path.exists(img_medal) else f"https://via.placeholder.com/150", use_container_width=True)
            
            with f1_c2:
                fig_agua = go.Figure(go.Indicator(
                    mode = "gauge+number", value = total_agua_total,
                    title = {'text': "Consumo Agua (L)", 'font': {'size': 20}},
                    gauge = {'axis': {'range': [0, st.session_state.t_agua_val]}, 'bar': {'color': "#0077B6"}}
                ))
                fig_agua.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=20))
                st.plotly_chart(fig_agua, use_container_width=True)
                st.metric("Progreso Agua", f"{pct_agua:.1f}%", delta=f"{total_agua_total:.1f} L actuales")

            with f1_c3:
                fig_luz = go.Figure(go.Indicator(
                    mode = "gauge+number", value = total_luz_total,
                    title = {'text': "Consumo Energía (kWh)", 'font': {'size': 20}},
                    gauge = {'axis': {'range': [0, st.session_state.t_luz_val]}, 'bar': {'color': "#FFB703"}}
                ))
                fig_luz.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=20))
                st.plotly_chart(fig_luz, use_container_width=True)
                st.metric("Progreso Energía", f"{pct_luz:.1f}%", delta=f"{total_luz_total:.1f} kWh actuales")

            # FILA 2: AGUA
            st.divider()
            f2_c1, f2_c23 = st.columns([1, 2])
            
            # Ejecutamos primero la columna derecha para procesar los filtros y la data
            with f2_c23:
                df_a_plot = df_recursos_base[['Date', 'Liters', 'Department']].copy() if not df_recursos_base.empty else pd.DataFrame()
                if not st.session_state.df_limpieza_sesion.empty:
                    d_l = st.session_state.df_limpieza_sesion.copy().rename(columns={'Water Consumed (Liters)':'Liters'})
                    d_l['Date'] = pd.to_datetime(d_l['Date']); d_l['Department'] = 'Limpieza'
                    df_a_plot = pd.concat([df_a_plot, d_l])
                if not st.session_state.df_otro_sesion.empty:
                    d_o = st.session_state.df_otro_sesion.copy().rename(columns={'Water Consumed (Liters)':'Liters','Timestamp':'Date','Equipment Name':'Department'})
                    d_o['Date'] = pd.to_datetime(d_o['Date'])
                    df_a_plot = pd.concat([df_a_plot, d_o])
                
                if not df_a_plot.empty:
                    sc1, sc2 = st.columns(2)
                    with sc1: temp_a = st.selectbox("Temporalidad", ["Diario", "Semanal"], key="ta")
                    with sc2: 
                        areas_a = ["Todas las áreas"] + list(df_a_plot['Department'].unique())
                        area_a = st.selectbox("Fuente", areas_a, key="aa")
                    if area_a != "Todas las áreas": df_a_plot = df_a_plot[df_a_plot['Department'] == area_a]
                    df_ag = df_a_plot.groupby(pd.Grouper(key='Date', freq='W-MON') if temp_a=="Semanal" else df_a_plot['Date'].dt.date)['Liters'].sum().reset_index()
                    df_ag.columns = ['Date', 'Liters']
                    st.plotly_chart(px.line(df_ag, x='Date', y='Liters', markers=True, title="Histórico Agua", color_discrete_sequence=["#0077B6"]), use_container_width=True)

            # Ahora renderizamos la columna izquierda usando los datos filtrados (df_a_plot)
            with f2_c1:
                st.write("### Predicción Agua (L)")
                df_pred_agua = generar_prediccion(df_a_plot, 'Date', 'Liters', 'sum')
                st.dataframe(df_pred_agua, use_container_width=True, hide_index=True)


            # FILA 3: ENERGÍA
            st.divider()
            f3_c12, f3_c3 = st.columns([2, 1])
            
            with f3_c12:
                df_l_plot = df_recursos_base[['Date', 'Electric Energy (kWh)', 'Department']].copy() if not df_recursos_base.empty else pd.DataFrame()
                if not st.session_state.df_otro_sesion.empty:
                    d_ol = st.session_state.df_otro_sesion.copy().rename(columns={'Energy Consumed (kWh)':'Electric Energy (kWh)','Timestamp':'Date','Equipment Name':'Department'})
                    d_ol['Date'] = pd.to_datetime(d_ol['Date'])
                    df_l_plot = pd.concat([df_l_plot, d_ol])
                
                if not df_l_plot.empty:
                    sc3, sc4 = st.columns(2)
                    with sc3: temp_l = st.selectbox("Temporalidad", ["Diario", "Semanal"], key="tl")
                    with sc4: 
                        areas_l = ["Todas las áreas"] + list(df_l_plot['Department'].unique())
                        area_l = st.selectbox("Fuente", areas_l, key="al")
                    if area_l != "Todas las áreas": df_l_plot = df_l_plot[df_l_plot['Department'] == area_l]
                    df_lg = df_l_plot.groupby(pd.Grouper(key='Date', freq='W-MON') if temp_l=="Semanal" else df_l_plot['Date'].dt.date)['Electric Energy (kWh)'].sum().reset_index()
                    df_lg.columns = ['Date', 'Electric Energy (kWh)']
                    st.plotly_chart(px.line(df_lg, x='Date', y='Electric Energy (kWh)', markers=True, title="Histórico Energía", color_discrete_sequence=["#FFB703"]), use_container_width=True)
            
            with f3_c3:
                st.write("### Predicción Energía (kWh)")
                df_pred_luz = generar_prediccion(df_l_plot, 'Date', 'Electric Energy (kWh)', 'sum')
                st.dataframe(df_pred_luz, use_container_width=True, hide_index=True)


            # FILA 4: CLIMA
            st.divider()
            f4_c1, f4_c23 = st.columns([1, 2])
            
            with f4_c23:
                file_path_clima = 'smartsus_clima.csv'
                df_clima_base = pd.read_csv(file_path_clima) if os.path.exists(file_path_clima) else pd.DataFrame()
                df_clima_plot = pd.DataFrame()
                if not df_clima_base.empty:
                    df_clima_base['Date'] = pd.to_datetime(df_clima_base['Date'])
                    df_clima_plot = df_clima_base.copy() # Variable paralela para predecir
                    f_clima = st.selectbox("Promedio Temperatura", ["Horario", "Diario", "Mensual"], key="ct")
                    if f_clima == "Mensual": df_cg = df_clima_base.groupby(pd.Grouper(key='Date', freq='MS'))['Temperature (°C)'].mean().reset_index()
                    elif f_clima == "Diario": df_cg = df_clima_base.groupby(df_clima_base['Date'].dt.date)['Temperature (°C)'].mean().reset_index()
                    else: df_cg = df_clima_base
                    df_cg.rename(columns={df_cg.columns[0]: 'Date'}, inplace=True)
                    st.plotly_chart(px.line(df_cg, x='Date', y='Temperature (°C)', title="Tendencia Clima", color_discrete_sequence=["#2ECC71"]), use_container_width=True)

            with f4_c1:
                st.write("### Predicción Clima (°C)")
                df_pred_clima = generar_prediccion(df_clima_plot, 'Date', 'Temperature (°C)', 'mean')
                st.dataframe(df_pred_clima, use_container_width=True, hide_index=True)


        # B. ENTRENAMIENTO
        elif st.session_state.pagina_actual == "entrenamiento":
            st.title("Centro de Entrenamiento")
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Subida de Archivos")
                f_limp = st.file_uploader("Limpieza (CSV)", type="csv")
                if f_limp: 
                    st.session_state.df_limpieza_sesion = pd.read_csv(f_limp)
                    if 'Date' in st.session_state.df_limpieza_sesion.columns:
                        st.session_state.df_limpieza_sesion['Date'] = pd.to_datetime(st.session_state.df_limpieza_sesion['Date'], errors='coerce')
                    st.success("Limpieza cargada.")
                
                f_equi = st.file_uploader("Otro (CSV - Equipos)", type="csv")
                if f_equi: 
                    st.session_state.df_otro_sesion = pd.read_csv(f_equi)
                    if 'Timestamp' in st.session_state.df_otro_sesion.columns:
                        st.session_state.df_otro_sesion['Timestamp'] = pd.to_datetime(st.session_state.df_otro_sesion['Timestamp'], errors='coerce')
                    st.success("Equipos cargados.")

            with c2:
                st.subheader("Estado Operativo")
                if pct_agua >= 90.0:
                    st.error(f"⚠️ **Alerta Crítica:** El consumo de agua ha alcanzado el {pct_agua:.1f}% de la meta. Se requiere revisión inmediata de protocolos operativos.")
                if pct_luz >= 90.0:
                    st.error(f"⚠️ **Alerta Crítica:** El consumo eléctrico ha alcanzado el {pct_luz:.1f}% de la meta. Se sugiere implementar medidas de contención.")
                
                if pct_agua < 90.0 and pct_luz < 90.0:
                    st.success("✅ Consumos dentro de los parámetros esperados.")

                st.divider()

                st.info("📊 Resumen de Actividades (Última Jornada Registrada):")
                df_limp = st.session_state.df_limpieza_sesion
                if not df_limp.empty and 'Date' in df_limp.columns:
                    ultimo_dia_limp = df_limp['Date'].max().date()
                    actividades_hoy_limp = df_limp[df_limp['Date'].dt.date == ultimo_dia_limp]
                    st.write(f"**🧹 Limpieza ({ultimo_dia_limp}):**")
                    posibles_nombres_area = ['Area', 'Department', 'Ubicacion', 'Lugar', 'Room']
                    col_area = next((col for col in posibles_nombres_area if col in actividades_hoy_limp.columns), None)
                    if not col_area and len(actividades_hoy_limp.columns) > 1:
                        col_area = actividades_hoy_limp.columns[1]
                    if col_area:
                        conteo_areas = actividades_hoy_limp[col_area].value_counts()
                        for area, conteo in conteo_areas.items():
                            st.write(f"- {area}: {conteo} intervenciones")
                    else:
                        st.write("*(No se pudo identificar la columna)*")
                else:
                    st.write("**🧹 Limpieza:** Sin datos recientes.")

                df_equi = st.session_state.df_otro_sesion
                if not df_equi.empty and 'Timestamp' in df_equi.columns:
                    ultimo_dia_equi = df_equi['Timestamp'].max().date()
                    actividades_hoy_equi = df_equi[df_equi['Timestamp'].dt.date == ultimo_dia_equi]
                    st.write(f"\n**⚙️ Mantenimiento ({ultimo_dia_equi}):**")
                    posibles_nombres_equipo = ['Equipment Name', 'Equipment', 'Equipo', 'Maquina']
                    col_equipo = next((col for col in posibles_nombres_equipo if col in actividades_hoy_equi.columns), None)
                    if not col_equipo and len(actividades_hoy_equi.columns) > 1:
                        col_equipo = actividades_hoy_equi.columns[1]
                    if col_equipo:
                        conteo_equipos = actividades_hoy_equi[col_equipo].value_counts()
                        for equipo, conteo in conteo_equipos.items():
                            st.write(f"- {equipo}: {conteo} horas operativas registradas")
                    else:
                        st.write("*(No se pudo identificar la columna)*")
                else:
                    st.write("**⚙️ Mantenimiento:** Sin datos recientes.")

        # C. USUARIO
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
        if st.button("Cerrar sesión", key="btn_logout"): cerrar_sesion()

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
            else: st.error("Error.")

if __name__ == "__main__":
    main()