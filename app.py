import streamlit as st
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import datetime # Para manejar los días de mañana y pasado
import time # Para controlar el refresco de 20 segundos
import requests # NUEVO: Para el chatbot
import json # NUEVO: Para el chatbot

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="SmartSUS - Dashboard Corporativo",
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- CONFIGURACIÓN DE IBM WATSONX (CHATBOT) ---
try:
    API_KEY_PERSISTENTE = st.secrets["ibm_watsonx_api_key"]
except KeyError:
    API_KEY_PERSISTENTE = "0LuuGwanJ4ObxoS076PL0kQpsjPqQ_j5za688DvuEqhb" # Fallback para evitar que se caiga en local

IAM_URL = "https://iam.cloud.ibm.com/identity/token"
CHAT_URL = "https://us-south.ml.cloud.ibm.com/ml/v1/text/chat?version=2023-05-29"
WATSONX_PROJECT_ID = "1a004ff5-3aec-4683-bea6-b3d93b0fabe8"
MODEL_ID = "ibm/granite-3-3-8b-instruct"

SYSTEM_MESSAGE_CONTENT = (
    "Eres un Asistente Experto de Soporte Técnico para la empresa SmartLog. "
    "Nuestra misión es ayudar a las empresas a gestionar recursos (agua y energía) con el slogan 'Manage, monitor, GROW'. "
    "Tu objetivo es asistir a los usuarios de la plataforma respondiendo dudas sobre cómo "
    "interpretar el dashboard, subir archivos CSV y resolver problemas de eficiencia.\n"
    "Mantén un tono profesional, conciso, amable y corporativo."
)

# --- 2. ESTILOS CSS ---
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
    .contacto-card { background-color: #f8f9fa; padding: 30px; border-radius: 10px; border-left: 5px solid #0077B6; color: #333;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. BASE DE DATOS DE USUARIOS ---
USUARIOS = {
    "TAVERA": {"password": "Emiliano", "desde": "12/05/2025", "empresa": "Hotel1", "foto": "foto1.jpg", "caducidad": "20D"},
    "Julio": {"password": "estralla15", "desde": "08/01/2024", "empresa": "manufacturera", "foto": "foto2.jpg", "caducidad": "10D"},
    "Juan": {"password": "cantar72", "desde": "09/07/2025", "empresa": "hotel2", "foto": "foto3.jpg", "caducidad": "80D"},
    "Andres": {"password": "1234", "desde": "01/01/2026", "empresa": "fábrica juguetes", "foto": "foto4.jpg", "caducidad": "3D"}
}

# --- 4. FUNCIONES AUXILIARES Y PREDICCIÓN ---
def cerrar_sesion():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

def generar_prediccion(df, col_fecha, col_valor, operacion='sum'):
    if df.empty or col_fecha not in df.columns or col_valor not in df.columns:
        return pd.DataFrame({"Día": ["Mañana", "Pasado mañana"], "Predicción Uso": [0.0, 0.0]})
    
    df_temp = df.copy()
    df_temp[col_fecha] = pd.to_datetime(df_temp[col_fecha]).dt.date
    
    if operacion == 'sum': df_grp = df_temp.groupby(col_fecha)[col_valor].sum().reset_index()
    else: df_grp = df_temp.groupby(col_fecha)[col_valor].mean().reset_index()
        
    df_grp = df_grp.sort_values(col_fecha).dropna(subset=[col_valor])
    
    if len(df_grp) < 2: 
        val = df_grp[col_valor].iloc[0] if len(df_grp) == 1 else 0.0
        return pd.DataFrame({"Día": ["Mañana", "Pasado mañana"], "Predicción Uso": [round(val, 1), round(val, 1)]})

    df_grp = df_grp.tail(14)
    x = np.arange(len(df_grp))
    y = df_grp[col_valor].values
    
    if np.all(y == y[0]): p1, p2 = y[0], y[0]
    else:
        z = np.polyfit(x, y, 1) 
        p = np.poly1d(z)
        p1 = p(len(df_grp))     
        p2 = p(len(df_grp) + 1) 
        
    ultimo_dia = df_grp[col_fecha].iloc[-1]
    dia1 = ultimo_dia + datetime.timedelta(days=1)
    dia2 = ultimo_dia + datetime.timedelta(days=2)
    
    return pd.DataFrame({
        "Día": [f"24Hrs ({dia1.strftime('%d/%m')})", f"48Hrs ({dia2.strftime('%d/%m')})"],
        "Predicción Uso": [max(0, round(p1, 1)), max(0, round(p2, 1))] 
    })

# --- FUNCIONES DEL CHATBOT ---
@st.cache_data(ttl=3540)
def get_iam_token(api_key):
    if api_key == "FALTA_API_KEY": return None
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    data = f"grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={api_key}"
    try:
        response = requests.post(IAM_URL, headers=headers, data=data, timeout=10)
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception: return None

def get_watsonx_chat_response(chat_history):
    bearer_token = get_iam_token(API_KEY_PERSISTENTE)
    if not bearer_token: return "El Asistente requiere configuración en st.secrets para responder. (Modo Local)"
    headers = {"Accept": "application/json", "Content-Type": "application/json", "Authorization": f"Bearer {bearer_token}"}
    body = {"messages": chat_history, "project_id": WATSONX_PROJECT_ID, "model_id": MODEL_ID, "frequency_penalty": 0, "max_tokens": 1000, "presence_penalty": 0, "temperature": 0, "top_p": 1}
    try:
        response = requests.post(CHAT_URL, headers=headers, json=body, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e: return "Error de conexión con el Asistente WatsonX."

# --- 5. LÓGICA PRINCIPAL ---
def main():
    if 'autenticado' not in st.session_state: st.session_state.autenticado = False
    if 'pagina_actual' not in st.session_state: st.session_state.pagina_actual = "dashboard"
    if 'df_limpieza_sesion' not in st.session_state: st.session_state.df_limpieza_sesion = pd.DataFrame()
    if 'df_otro_sesion' not in st.session_state: st.session_state.df_otro_sesion = pd.DataFrame()
    if 't_agua_val' not in st.session_state: st.session_state.t_agua_val = 50000000.0  
    if 't_luz_val' not in st.session_state: st.session_state.t_luz_val = 50000000.0   
    if 'storm_idx' not in st.session_state: st.session_state.storm_idx = 0
    if 'last_update' not in st.session_state: st.session_state.last_update = time.time()
    
    # Historial del Chatbot
    if "chatbot_messages" not in st.session_state:
        st.session_state.chatbot_messages = [
            {"role": "system", "content": SYSTEM_MESSAGE_CONTENT},
            {"role": "assistant", "content": "¡Hola! Soy tu asistente de **SmartLog**. ¿En qué te puedo ayudar hoy con tu gestión de recursos?"}
        ]

    if not st.session_state.autenticado:
        mostrar_login()
    else:
        # Refresco de 20 segundos (Dashboard y Entrenamiento)
        if st.session_state.pagina_actual in ["dashboard", "entrenamiento"]:
            ahora = time.time()
            if ahora - st.session_state.last_update >= 20:
                st.session_state.storm_idx = (st.session_state.storm_idx + 1) % 99 
                st.session_state.last_update = ahora
                st.rerun()

        # NAVEGACIÓN
        cols_nav = st.columns(4)
        secciones = ["Dashboard", "Entrenamiento", "Usuario", "Cuarta"]
        for i, seccion in enumerate(secciones):
            with cols_nav[i]:
                btn_name = "Soporte" if seccion == "Cuarta" else seccion # Renombramos el botón visualmente
                if st.button(btn_name, key=f"nav_btn_{seccion}_{i}"):
                    st.session_state.pagina_actual = seccion.lower()
                    st.rerun()
        st.divider()

        user_info = USUARIOS.get(st.session_state.user_name, {})
        
        # CARGA DE DATOS
        file_path_recursos = 'smartsus_simulated_resources.csv'
        if os.path.exists(file_path_recursos):
            df_recursos_base = pd.read_csv(file_path_recursos)
            df_recursos_base['Date'] = pd.to_datetime(df_recursos_base['Date'])
            total_agua_base = df_recursos_base['Liters'].sum()
            total_luz_base = df_recursos_base['Electric Energy (kWh)'].sum()
        else:
            df_recursos_base = pd.DataFrame()
            total_agua_base, total_luz_base = 0, 0

        # Validaciones para evitar KeyError en archivos subidos
        total_agua_limp = st.session_state.df_limpieza_sesion['Water Consumed (Liters)'].sum() if not st.session_state.df_limpieza_sesion.empty and 'Water Consumed (Liters)' in st.session_state.df_limpieza_sesion.columns else 0
        total_agua_equi = st.session_state.df_otro_sesion['Water Consumed (Liters)'].sum() if not st.session_state.df_otro_sesion.empty and 'Water Consumed (Liters)' in st.session_state.df_otro_sesion.columns else 0
        total_luz_equi = st.session_state.df_otro_sesion['Energy Consumed (kWh)'].sum() if not st.session_state.df_otro_sesion.empty and 'Energy Consumed (kWh)' in st.session_state.df_otro_sesion.columns else 0

        total_agua_total = total_agua_base + total_agua_limp + total_agua_equi
        total_luz_total = total_luz_base + total_luz_equi

        pct_agua = (total_agua_total / st.session_state.t_agua_val) * 100 if st.session_state.t_agua_val > 0 else 0
        pct_luz = (total_luz_total / st.session_state.t_luz_val) * 100 if st.session_state.t_luz_val > 0 else 0

        # ==========================================
        # A. DASHBOARD
        # ==========================================
        if st.session_state.pagina_actual == "dashboard":
            
            with st.expander("Configurar Objetivos Anuales (Targets)"):
                col_t1, col_t2 = st.columns(2)
                with col_t1: st.session_state.t_agua_val = st.number_input("Meta Agua (L)", value=st.session_state.t_agua_val, step=100.0)
                with col_t2: st.session_state.t_luz_val = st.number_input("Meta Energía (kWh)", value=st.session_state.t_luz_val, step=50.0)

            # FILA 1: Medalla y Gauges
            f1_c1, f1_c2, f1_c3 = st.columns(3)
            with f1_c1:
                img_medal = "gold.jpeg" if st.session_state.user_name == "TAVERA" else ("plata.jpeg" if st.session_state.user_name == "Julio" else "bronce.jpeg")
                _, col_img, _ = st.columns([1, 2, 1])
                with col_img: st.image(img_medal if os.path.exists(img_medal) else f"https://via.placeholder.com/150", use_container_width=True)
            
            with f1_c2:
                fig_agua = go.Figure(go.Indicator(mode = "gauge+number", value = total_agua_total, title = {'text': "Consumo Agua (L)", 'font': {'size': 20}}, gauge = {'axis': {'range': [0, st.session_state.t_agua_val]}, 'bar': {'color': "#0077B6"}}))
                fig_agua.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=20))
                st.plotly_chart(fig_agua, use_container_width=True)
                st.metric("Progreso Agua", f"{pct_agua:.1f}%", delta=f"{total_agua_total:.1f} L actuales")

            with f1_c3:
                fig_luz = go.Figure(go.Indicator(mode = "gauge+number", value = total_luz_total, title = {'text': "Consumo Energía (kWh)", 'font': {'size': 20}}, gauge = {'axis': {'range': [0, st.session_state.t_luz_val]}, 'bar': {'color': "#FFB703"}}))
                fig_luz.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=20))
                st.plotly_chart(fig_luz, use_container_width=True)
                st.metric("Progreso Energía", f"{pct_luz:.1f}%", delta=f"{total_luz_total:.1f} kWh actuales")

            # FILA 2: AGUA
            st.divider()
            f2_c1, f2_c23 = st.columns([1, 2])
            with f2_c23:
                df_a_plot = df_recursos_base[['Date', 'Liters', 'Department']].copy() if not df_recursos_base.empty else pd.DataFrame()
                if not st.session_state.df_limpieza_sesion.empty and 'Water Consumed (Liters)' in st.session_state.df_limpieza_sesion.columns:
                    d_l = st.session_state.df_limpieza_sesion.copy().rename(columns={'Water Consumed (Liters)':'Liters'})
                    d_l['Date'] = pd.to_datetime(d_l['Date']); d_l['Department'] = 'Limpieza'
                    df_a_plot = pd.concat([df_a_plot, d_l[['Date', 'Liters', 'Department']]])
                if not st.session_state.df_otro_sesion.empty and 'Water Consumed (Liters)' in st.session_state.df_otro_sesion.columns:
                    d_o = st.session_state.df_otro_sesion.copy().rename(columns={'Water Consumed (Liters)':'Liters','Timestamp':'Date','Equipment Name':'Department'})
                    d_o['Date'] = pd.to_datetime(d_o['Date'])
                    df_a_plot = pd.concat([df_a_plot, d_o[['Date', 'Liters', 'Department']]])
                
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

            with f2_c1:
                st.write("### Predicción Agua (L)")
                df_pred_agua = generar_prediccion(df_a_plot, 'Date', 'Liters', 'sum')
                st.dataframe(df_pred_agua, use_container_width=True, hide_index=True)

            # FILA 3: ENERGÍA
            st.divider()
            f3_c12, f3_c3 = st.columns([2, 1])
            with f3_c12:
                df_l_plot = df_recursos_base[['Date', 'Electric Energy (kWh)', 'Department']].copy() if not df_recursos_base.empty else pd.DataFrame()
                if not st.session_state.df_otro_sesion.empty and 'Energy Consumed (kWh)' in st.session_state.df_otro_sesion.columns:
                    d_ol = st.session_state.df_otro_sesion.copy().rename(columns={'Energy Consumed (kWh)':'Electric Energy (kWh)','Timestamp':'Date','Equipment Name':'Department'})
                    d_ol['Date'] = pd.to_datetime(d_ol['Date'])
                    df_l_plot = pd.concat([df_l_plot, d_ol[['Date', 'Electric Energy (kWh)', 'Department']]])
                
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

            # FILA 4: CLIMA Y TORMENTAS 
            st.divider()
            f4_c1, f4_c23 = st.columns([1, 2])
            
            with f4_c1:
                st.write("### Monitoreo de Tormentas")
                if os.path.exists('datos_pronostico_tormentas.csv'):
                    df_storm = pd.read_csv('datos_pronostico_tormentas.csv')
                    idx = st.session_state.storm_idx
                    if idx + 1 < len(df_storm):
                        rec1 = df_storm.iloc[idx]; rec2 = df_storm.iloc[idx + 1]
                        data_transposed = {"Variable": [str(x) for x in rec1.index], f"ID {rec1.iloc[0]}": [str(x) for x in rec1.values], f"ID {rec2.iloc[0]}": [str(x) for x in rec2.values]}
                        st.dataframe(pd.DataFrame(data_transposed), use_container_width=True, hide_index=True)
                        st.caption(f"Actualizando cada 20s. Registros actuales: {idx+1} y {idx+2}")
                    else: st.write("Fin de los registros.")
                else: st.warning("El archivo 'datos_pronostico_tormentas.csv' no se encuentra disponible.")
                
            

            with f4_c23:
                df_clima_base = pd.read_csv('smartsus_clima.csv') if os.path.exists('smartsus_clima.csv') else pd.DataFrame()
                if not df_clima_base.empty:
                    df_clima_base['Date'] = pd.to_datetime(df_clima_base['Date'])
                    f_clima = st.selectbox(" ", ["Horario", "Diario", "Mensual"], key="ct")
                    if f_clima == "Mensual": df_cg = df_clima_base.groupby(pd.Grouper(key='Date', freq='MS'))['Temperature (°C)'].mean().reset_index()
                    elif f_clima == "Diario": df_cg = df_clima_base.groupby(df_clima_base['Date'].dt.date)['Temperature (°C)'].mean().reset_index()
                    else: df_cg = df_clima_base.copy()
                    df_cg.rename(columns={df_cg.columns[0]: 'Date'}, inplace=True)
                    st.plotly_chart(px.line(df_cg, x='Date', y='Temperature (°C)', title="Tendencia Clima", color_discrete_sequence=["#2ECC71"]), use_container_width=True)

        # ==========================================
        # B. ENTRENAMIENTO
        # ==========================================
        elif st.session_state.pagina_actual == "entrenamiento":
            st.title("Centro de Entrenamiento")
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Subida de Archivos")
                f_limp = st.file_uploader("Limpieza (CSV)", type="csv")
                if f_limp: 
                    st.session_state.df_limpieza_sesion = pd.read_csv(f_limp)
                    if 'Date' in st.session_state.df_limpieza_sesion.columns: st.session_state.df_limpieza_sesion['Date'] = pd.to_datetime(st.session_state.df_limpieza_sesion['Date'], errors='coerce')
                    st.success("Limpieza cargada.")
                f_equi = st.file_uploader("Otro (CSV - Equipos)", type="csv")
                if f_equi: 
                    st.session_state.df_otro_sesion = pd.read_csv(f_equi)
                    if 'Timestamp' in st.session_state.df_otro_sesion.columns: st.session_state.df_otro_sesion['Timestamp'] = pd.to_datetime(st.session_state.df_otro_sesion['Timestamp'], errors='coerce')
                    st.success("Equipos cargados.")

            with c2:
                # ALERTA ROJA GIGANTE (TORMENTA INMINENTE)
                if os.path.exists('datos_pronostico_tormentas.csv'):
                    df_storm_alert = pd.read_csv('datos_pronostico_tormentas.csv')
                    idx_alert = st.session_state.storm_idx
                    if idx_alert < len(df_storm_alert) and 'condicion_objetivo' in df_storm_alert.columns:
                        if str(df_storm_alert.iloc[idx_alert]['condicion_objetivo']).strip() == "Tormenta Inminente":
                            st.markdown("""
                                <div style='background-color: #ff4b4b; padding: 20px; border-radius: 10px; margin-bottom: 20px; text-align: center; border: 2px solid darkred;'>
                                    <h2 style='color: white; margin: 0; font-weight: 900;'>🚨 ¡Tormenta Inminente, se han cancelado reservas! 🚨</h2>
                                </div>
                            """, unsafe_allow_html=True)
                
                st.subheader("Estado Operativo")
                if pct_agua >= 90.0: st.error(f"⚠️ **Alerta Crítica:** Consumo de agua al {pct_agua:.1f}%.")
                if pct_luz >= 90.0: st.error(f"⚠️ **Alerta Crítica:** Consumo eléctrico al {pct_luz:.1f}%.")
                if pct_agua < 90.0 and pct_luz < 90.0: st.success(" Consumos dentro de los parámetros esperados.")

                st.divider()

                st.info(" Resumen de Actividades (Última Jornada Registrada):")
                df_limp = st.session_state.df_limpieza_sesion
                if not df_limp.empty and 'Date' in df_limp.columns:
                    ultimo_dia_limp = df_limp['Date'].max().date()
                    actividades_hoy_limp = df_limp[df_limp['Date'].dt.date == ultimo_dia_limp]
                    st.write(f"** Limpieza ({ultimo_dia_limp}):**")
                    posibles_nombres_area = ['Area', 'Department', 'Ubicacion', 'Lugar', 'Room']
                    col_area = next((col for col in posibles_nombres_area if col in actividades_hoy_limp.columns), None)
                    if not col_area and len(actividades_hoy_limp.columns) > 1: col_area = actividades_hoy_limp.columns[1]
                    if col_area:
                        for area, conteo in actividades_hoy_limp[col_area].value_counts().items(): st.write(f"- {area}: {conteo} intervenciones")
                    else: st.write("*(No se pudo identificar la columna)*")
                else: st.write("** Limpieza:** Sin datos recientes.")

                df_equi = st.session_state.df_otro_sesion
                if not df_equi.empty and 'Timestamp' in df_equi.columns:
                    ultimo_dia_equi = df_equi['Timestamp'].max().date()
                    actividades_hoy_equi = df_equi[df_equi['Timestamp'].dt.date == ultimo_dia_equi]
                    st.write(f"\n** Mantenimiento ({ultimo_dia_equi}):**")
                    posibles_nombres_equipo = ['Equipment Name', 'Equipment', 'Equipo', 'Maquina']
                    col_equipo = next((col for col in posibles_nombres_equipo if col in actividades_hoy_equi.columns), None)
                    if not col_equipo and len(actividades_hoy_equi.columns) > 1: col_equipo = actividades_hoy_equi.columns[1]
                    if col_equipo:
                        for equipo, conteo in actividades_hoy_equi[col_equipo].value_counts().items(): st.write(f"- {equipo}: {conteo} horas operativas registradas")
                    else: st.write("*(No se pudo identificar la columna)*")
                else: st.write("** Mantenimiento:** Sin datos recientes.")

        # ==========================================
        # C. USUARIO
        # ==========================================
        elif st.session_state.pagina_actual == "usuario":
            _, col_p, _ = st.columns([0.15, 0.7, 0.15])
            with col_p:
                st.markdown("<div class='perfil-titulo'>Perfil de Usuario</div>", unsafe_allow_html=True)
                c_img, c_txt = st.columns([0.5, 2.0])
                with c_img: st.image(user_info.get('foto', 'https://via.placeholder.com/200'), use_container_width=True)
                with c_txt:
                    st.markdown(f"<div class='perfil-dato'><b>Nombre:</b> {st.session_state.user_name}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='perfil-dato'><b>Empresa:</b> {user_info.get('empresa', '')}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='perfil-dato'><b>Usuario desde:</b> {user_info.get('desde', '')}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='perfil-dato'><b>Caducidad de cuenta:</b> {user_info.get('caducidad', '')}</div>", unsafe_allow_html=True)  

        # ==========================================
        # D. CUARTA (SOPORTE Y CONTACTO)
        # ==========================================
        elif st.session_state.pagina_actual == "cuarta":
            st.title("Centro de Soporte")
            col_cont, col_chat = st.columns([1, 1.5])
            
            with col_cont:
                st.markdown("""
                <div class="contacto-card">
                    <h2 style='color:#0077B6; margin-bottom: 0px;'>SmartLog</h2>
                    <h4 style='color:#555; font-style:italic; margin-top: 0px;'>Manage, monitor, GROW.</h4>
                    <hr>
                    <p><b>📍 Sede Central:</b><br>Av. Paseo de la Reforma 123, Piso 14<br>Juárez, Cuauhtémoc, 06600 Ciudad de México, CDMX</p>
                    <p><b>📧 Correo Electrónico:</b><br>soporte.tecnico@smartlog.mx</p>
                    <p><b>📞 Líneas de Atención:</b></p>
                    <ul>
                        <li>Ventas: +52 (55) 1234-5678</li>
                        <li>Soporte Técnico: +52 (55) 9876-5432</li>
                        <li>Emergencias 24/7: +52 (55) 5555-4444</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

            with col_chat:
                st.subheader("Chat Asistente Virtual")
                
                # Mostrar historial
                for msg in st.session_state.chatbot_messages:
                    if msg["role"] != "system":
                        with st.chat_message(msg["role"]):
                            st.markdown(msg["content"])
                
                # Input de usuario
                if prompt := st.chat_input("Escribe tu duda aquí..."):
                    with st.chat_message("user"): st.markdown(prompt)
                    st.session_state.chatbot_messages.append({"role": "user", "content": prompt})
                    
                    with st.spinner("Analizando consulta..."):
                        respuesta = get_watsonx_chat_response(st.session_state.chatbot_messages)
                    
                    with st.chat_message("assistant"): st.markdown(respuesta)
                    st.session_state.chatbot_messages.append({"role": "assistant", "content": respuesta})

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
