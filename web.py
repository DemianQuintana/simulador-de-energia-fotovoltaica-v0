import streamlit as st
import pandas as pd
import requests
import altair as alt

from motor import calcular_generacion

MESES_CORTOS = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",]

if "lat" not in st.session_state:
    st.session_state.lat = -31.6475
    st.session_state.lon = -60.6985
if "vista_activa" not in st.session_state:
    st.session_state.vista_activa = "ubicacion"
if "mensaje_exito" not in st.session_state:
    st.session_state.mensaje_exito = None

st.set_page_config(layout="wide")

st.title("Simulador de Energia Fotovoltaica ☀️")

with st.sidebar:
    st.title("📋Datos del sistema")
    potAC = st.number_input("Potencia del inversor (kW)", min_value=0.0, step=0.1)
    potDC = st.number_input("Potencia total de los paneles (kW)", min_value=0.0, step=0.05)
    betha = st.number_input("Inclinacion de los paneles (grados)", min_value=30, max_value=90, step=1)
    azimuth = st.number_input("Azimuth (grados)", min_value=0, max_value=360, step=1)
    tipoPanel = st.selectbox("Tipo de panel", ("Estandar", "Premium"))
    perdidas = st.number_input("Perdidas del sistema (%)", value=14.08, min_value=10.0, max_value=30.0, step=0.1)
    calcular = st.button("Calcular", use_container_width=True)

col_vista_1, col_vista_2 = st.columns(2)
with col_vista_1:
    if st.button("📍Ubicacion", use_container_width=True):
        st.session_state.vista_activa = "ubicacion"
with col_vista_2:
    if st.button("📊Resultados", use_container_width=True):
        st.session_state.vista_activa = "resultados"

if calcular:
    inputs = {
        "lat": st.session_state.lat,
        "lon": st.session_state.lon,
        "betha": betha,
        "azimuth": azimuth,
        "pot_dc": potDC,
        "pot_ac": potAC,
        "tipo_panel": tipoPanel,
        "perdidas": perdidas
    }

    try:
        resultados = calcular_generacion(inputs)
        st.session_state["resultados"] = resultados
        st.session_state.vista_activa = "resultados"
        st.rerun()
    except ValueError as error:
        st.error(str(error))

if st.session_state.vista_activa == "ubicacion":
    col1A, col1B = st.columns([4, 1])
    with col1A:
        direccion = st.text_input("Ubicacion del sistema")

    with col1B:
        st.markdown("<br>", unsafe_allow_html=True)
        ubicar = st.button("Ubicar", use_container_width=True)

    if ubicar and direccion:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": direccion + ", Santa Fe, Argentina",
            "format": "json"
        }

        headers = {
            "User-Agent": "simulador-fv"
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data:
                st.session_state.lat = float(data[0]["lat"])
                st.session_state.lon = float(data[0]["lon"])
            else:
                st.error("No se encontraron coordenadas para esa direccion.")
        except requests.Timeout:
            st.error("La consulta de ubicacion tardo demasiado. Intenta nuevamente.")
        except requests.RequestException:
            st.error("No se pudieron obtener los datos de ubicacion. Verifica tu conexion o intenta mas tarde.")
        except (KeyError, ValueError, TypeError):
            st.error("La respuesta del servicio de ubicacion no pudo procesarse correctamente.")

    df_mapa = pd.DataFrame({
        "lat": [st.session_state.lat],
        "lon": [st.session_state.lon]
    })

    st.map(df_mapa, size=22, zoom=15)

if st.session_state.vista_activa == "resultados":
    st.header("Resultados de la simulacion")

    if st.session_state.mensaje_exito:
        st.success(st.session_state.mensaje_exito)
        st.session_state.mensaje_exito = None

    if "resultados" not in st.session_state:
        st.info("Ejecuta una simulacion para ver los resultados.")
    else:
        res = st.session_state["resultados"]
        df_mensual = pd.DataFrame(res["energia_mensual"])
        df_mensual = df_mensual.sort_values("mes").reset_index(drop=True)
        df_mensual["Mes"] = MESES_CORTOS
        df_mensual["Energia (kWh)"] = df_mensual["energia"].round(2)
        df_grafico = df_mensual[["Mes", "Energia (kWh)"]]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Energia anual (kWh)", round(res["energia_anual"], 2))
        with col2:
            st.metric("Factor de capacidad (%)", round(res["factor_capacidad"], 2))
        with col3:
            st.metric(
                "Coordenada del dataset",
                f'{res["latitud_dataset"]:.4f}, {res["longitud_dataset"]:.4f}'
            )

        st.subheader("Generacion mensual")
        grafico_mensual = (
            alt.Chart(df_grafico)
            .mark_bar()
            .encode(
                x=alt.X("Mes:N", sort=MESES_CORTOS, title="Mes"),
                y=alt.Y("Energia (kWh):Q", title="Energia (kWh)")
            )
        )
        st.altair_chart(grafico_mensual, use_container_width=True)
        st.dataframe(df_grafico, use_container_width=True, hide_index=True)
