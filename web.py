import altair as alt
import pandas as pd
import requests
import streamlit as st

from motor import calcular_generacion

MESES_CORTOS = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


@st.cache_data(ttl=86400, show_spinner=False)
def buscar_coordenadas(direccion):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": f"{direccion}, Santa Fe, Argentina",
        "countrycodes": "ar",
        "format": "jsonv2",
        "limit": 1,
        "addressdetails": 1,
    }
    headers = {
        "User-Agent": "simulador-de-energia-fotovoltaica-v0/1.0 (contacto: demian.quintana.dq@gmail.com)",
        "Accept-Language": "es",
    }

    response = requests.get(url, params=params, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()

    if not data:
        return None

    return float(data[0]["lat"]), float(data[0]["lon"])


if "lat" not in st.session_state:
    st.session_state.lat = -31.6475
    st.session_state.lon = -60.6985

if "vista_activa" not in st.session_state:
    st.session_state.vista_activa = "ubicacion"

if "mensaje_exito" not in st.session_state:
    st.session_state.mensaje_exito = None

st.set_page_config(layout="wide")

st.title("Simulador de Energia Fotovoltaica")

with st.sidebar:
    st.title("Datos del sistema")
    potAC = st.number_input("Potencia del inversor (kW)", min_value=0.0, step=0.1)
    potDC = st.number_input("Potencia total de los paneles (kW)", min_value=0.0, step=0.05)
    betha = st.number_input("Inclinacion de los paneles (grados)", min_value=0, max_value=90, step=1)
    azimuth = st.number_input("Azimuth (grados)", min_value=0, max_value=360, step=1)
    tipoPanel = st.selectbox("Tipo de panel", ("Estandar", "Premium"))
    perdidas = st.number_input("Perdidas del sistema (%)", value=14.08, min_value=10.0, max_value=30.0, step=0.1)
    calcular = st.button("Calcular", use_container_width=True)

col_vista_1, col_vista_2 = st.columns(2)

with col_vista_1:
    if st.button("Ubicacion", use_container_width=True):
        st.session_state.vista_activa = "ubicacion"

with col_vista_2:
    if st.button("Resultados", use_container_width=True):
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
        "perdidas": perdidas,
    }

    try:
        resultados = calcular_generacion(inputs)
        st.session_state["resultados"] = resultados
        st.session_state.vista_activa = "resultados"
        st.session_state.mensaje_exito = "Simulacion calculada correctamente."
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
        try:
            coordenadas = buscar_coordenadas(direccion)
            if coordenadas:
                st.session_state.lat, st.session_state.lon = coordenadas
            else:
                st.error("No se encontraron coordenadas para esa ubicacion.")
        except requests.Timeout as error:
            st.error(f"Timeout al consultar ubicacion: {error}")
        except requests.HTTPError as error:
            respuesta = error.response
            detalle = respuesta.text[:300] if respuesta is not None else str(error)
            codigo = respuesta.status_code if respuesta is not None else "sin_codigo"
            st.error(f"Error HTTP {codigo} al consultar ubicacion: {detalle}")
        except requests.RequestException as error:
            st.error(f"Error de red al consultar ubicacion: {error}")
        except Exception as error:
            st.error(f"Error inesperado al consultar ubicacion: {error}")

    df_mapa = pd.DataFrame({
        "lat": [st.session_state.lat],
        "lon": [st.session_state.lon],
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
                f'{res["latitud_dataset"]:.4f}, {res["longitud_dataset"]:.4f}',
            )

        st.subheader("Generacion mensual")

        grafico_mensual = (
            alt.Chart(df_grafico)
            .mark_bar()
            .encode(
                x=alt.X("Mes:N", sort=MESES_CORTOS, title="Mes"),
                y=alt.Y("Energia (kWh):Q", title="Energia (kWh)"),
            )
        )

        st.altair_chart(grafico_mensual, use_container_width=True)
        st.dataframe(df_grafico, use_container_width=True, hide_index=True)
