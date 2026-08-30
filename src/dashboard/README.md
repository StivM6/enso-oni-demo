# Dashboard (Streamlit)

Presentacion del area privada (requiere login). **Regla clave:** las paginas
solo muestran datos; NO contienen logica de negocio. Toda consulta o calculo
se delega a `src/` (pipeline) o a la API.

- `app.py`           : entrada + login (streamlit-authenticator)
- `auth.py`          : configuracion de autenticacion
- `pages/`           : vistas (ENSO, precipitacion, riesgo)

Ejecutar local:  `streamlit run src/dashboard/app.py`
