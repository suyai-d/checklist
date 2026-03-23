import streamlit as st
import pandas as pd
import base64

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Checklist Pre-Campaña JD | Conci", layout="wide", page_icon="🚜")


# --- FUNCIÓN PARA LOGOS EN CABECERA ---
def render_header():
    try:
        with open("CSC.png", "rb") as f:
            csc_encoded = base64.b64encode(f.read()).decode()
        with open("JD.png", "rb") as f:
            jd_encoded = base64.b64encode(f.read()).decode()

        header_html = f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 2px solid #367c2b; margin-bottom: 20px;">
                <img src="data:image/png;base64,{csc_encoded}" style="height: 60px; margin-left: 10px;">
                <h1 style="margin: 0; color: #367c2b; font-family: sans-serif;">Reporte Técnico Checklist</h1>
                <img src="data:image/png;base64,{jd_encoded}" style="height: 60px; margin-right: 10px;">
            </div>
        """
        st.markdown(header_html, unsafe_allow_html=True)
    except FileNotFoundError:
        st.title("Reporte Técnico Checklist")


st.markdown("""
    <style>
    .metric-container {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e6e9ef;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

render_header()

# --- SIDEBAR ---
st.sidebar.header("Configuración ⚙️")
uploaded_file = st.sidebar.file_uploader("Subí el Excel de Emparejamientos", type=["xlsx"])
razon_social = st.sidebar.text_input("Razón Social del Cliente")
fecha_control = st.sidebar.date_input("Fecha de Control")

if razon_social:
    st.info(f"📋 **Cliente:** {razon_social}  |  📆 **Fecha de Control:** {fecha_control.strftime('%d/%m/%Y')}")

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, sheet_name="Emparejamientos")
    df.columns = df.columns.str.strip()
    equipos = df['Nombre de emparejamiento'].dropna().unique()
    total_equipos = len(equipos)

    # --- LÓGICA DE CÁLCULO ---
    puntos_totales_act = 0
    puntos_logrados_act = 0
    maquinas_con_monitoreo = 0

    for i in range(total_equipos):
        # 1. Monitor
        est_m = st.session_state.get(f"sel_m_{i}", "❌ Desactualizado")
        if "Actualizado" in est_m:
            puntos_totales_act += 1
            puntos_logrados_act += 1
        elif "Desactualizado" in est_m:
            puntos_totales_act += 1

        # 2. Receptor
        est_r = st.session_state.get(f"sel_r_{i}", "❌ Desactualizado")
        if "Actualizado" in est_r:
            puntos_totales_act += 1
            puntos_logrados_act += 1
        elif "Desactualizado" in est_r:
            puntos_totales_act += 1

        # 3. Unidades de Control
        cant_uc = st.session_state.get(f"uc_{i}", 0)
        est_g = st.session_state.get(f"eg_{i}", "❌ Desactualizado")
        if "No posee" not in est_g and cant_uc > 0:
            puntos_totales_act += cant_uc
            if "Actualizado" in est_g:
                puntos_logrados_act += cant_uc

        # 4. Monitoreo
        paq_m = st.session_state.get(f"pm_{i}", "⚪ No posee")
        if "Vigente" in paq_m:
            maquinas_con_monitoreo += 1

    pct_actualizacion = (puntos_logrados_act / puntos_totales_act * 100) if puntos_totales_act > 0 else 0
    pct_monitoreo = (maquinas_con_monitoreo / total_equipos * 100) if total_equipos > 0 else 0

    # --- TERMÓMETROS ---
    c_ind1, c_ind2 = st.columns(2)


    def get_color_hex(pct):
        if pct < 60:
            return "#FF4B4B"
        elif pct < 80:
            return "#FFBD45"
        else:
            return "#09AB3B"


    with c_ind1:
        st.markdown(
            f'<div class="metric-container"><h4>🌡️ Estado Gral de los Componentes</h4><h2 style="color:{get_color_hex(pct_actualizacion)}">{pct_actualizacion:.1f}%</h2></div>',
            unsafe_allow_html=True)
        st.progress(pct_actualizacion / 100)
    with c_ind2:
        st.markdown(
            f'<div class="metric-container"><h4>📡 Máquinas con paquete de Monitoreo del CSC</h4><h2 style="color:{get_color_hex(pct_monitoreo)}">{pct_monitoreo:.1f}%</h2></div>',
            unsafe_allow_html=True)
        st.progress(pct_monitoreo / 100)

    st.markdown("---")

    # --- TABLA ---
    anchos = [1.2, 0.8, 0.8, 1, 0.8, 0.8, 1, 0.8, 1.1, 1.1]
    cols_h = st.columns(anchos)
    for col, text in zip(cols_h,
                         ["Equipo", "Monitor", "Soft. M", "Estado M", "Receptor", "Soft. R", "Estado R", "Cant. UC",
                          "Estado Gral", "Paq. Monit"]):
        col.write(f"**{text}**")

    st.markdown("---")

    opciones_est = ["❌ Desactualizado", "✅ Actualizado", "⚪ Sin comp."]
    # Nueva lista de opciones para monitoreo
    opciones_paq = ["⚪ No posee", "🟢 Vigente", "🟡 Por Vencer", "🔴 Vencido"]

    for i, equipo in enumerate(equipos):
        info_equipo = df[df['Nombre de emparejamiento'] == equipo]
        sn_maquina = info_equipo['Número de serie de emparejamiento'].iloc[0]

        mon_info = info_equipo[info_equipo['Tipo'].str.contains('Monitor', case=False, na=False)]
        mod_mon = mon_info['Modelo'].iloc[0] if not mon_info.empty else "N/D"
        sw_mon = mon_info['Versión de software'].iloc[0] if not mon_info.empty else "-"

        rec_info = info_equipo[info_equipo['Tipo'].str.contains('Receptor', case=False, na=False)]
        mod_rec = rec_info['Modelo'].iloc[0] if not rec_info.empty else "N/D"
        sw_rec = rec_info['Versión de software'].iloc[0] if not rec_info.empty else "-"

        c = st.columns(anchos)
        with c[0]:
            st.write(f"**{equipo}**")
            st.caption(f"{sn_maquina}")
        with c[1]: st.write(mod_mon)
        with c[2]: st.write(sw_mon)

        # Estado Monitor: Comienza en Desactualizado (0) o Sin comp (2)
        with c[3]:
            def_m = 2 if mod_mon == "N/D" else 0
            st.selectbox(f"m_{i}", opciones_est, index=def_m, label_visibility="collapsed", key=f"sel_m_{i}")

        with c[4]: st.write(mod_rec)
        with c[5]: st.write(sw_rec)

        # Estado Receptor: Comienza en Desactualizado (0) o Sin comp (2)
        with c[6]:
            def_r = 2 if mod_rec == "N/D" else 0
            st.selectbox(f"r_{i}", opciones_est, index=def_r, label_visibility="collapsed", key=f"sel_r_{i}")

        with c[7]: st.number_input(f"uc_{i}", min_value=0, step=1, label_visibility="collapsed", key=f"uc_{i}")

        # Estado General UC: Comienza en Desactualizado (0)
        with c[8]: st.selectbox(f"eg_{i}", ["❌ Desactualizado", "✅ Actualizado", "⚪ No posee"], index=0,
                                label_visibility="collapsed", key=f"eg_{i}")

        # Paquete Monitoreo: Comienza en No Posee (index 0) y tiene "Por Vencer"
        with c[9]: st.selectbox(f"pm_{i}", opciones_paq, index=0, label_visibility="collapsed", key=f"pm_{i}")

        st.markdown("<hr style='margin:0; opacity:0.1'>", unsafe_allow_html=True)

    st.button("🔄 Recalcular")
else:
    st.info("👋 Cargá el Excel para empezar.")
