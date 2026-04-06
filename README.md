# Simulador de Energia Fotovoltaica

Aplicacion web desarrollada con Streamlit para estimar la generacion energetica de un sistema fotovoltaico en la provincia de Santa Fe, Argentina.

## Que hace

- Permite ubicar el sistema a partir de una direccion.
- Busca la coordenada mas cercana dentro de un dataset solar local.
- Calcula la generacion mensual y anual del sistema.
- Muestra factor de capacidad y resultados en grafico.

## Archivos principales

- `web.py`: interfaz web en Streamlit.
- `motor.py`: logica de simulacion fotovoltaica.
- `dataset_solar_santa_fe_LOCAL.parquet`: dataset local usado para los calculos.

## Ejecutar localmente

1. Instalar dependencias:

```bash
pip install -r requirements.txt
```

2. Ejecutar la app:

```bash
streamlit run web.py
```

## Deploy

Este proyecto esta pensado para desplegarse en Streamlit Community Cloud.
