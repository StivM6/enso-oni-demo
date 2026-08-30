"""Configuracion de autenticacion del dashboard.

En el MVP los usuarios y su suscripcion se gestionan en PostGIS y se
aprovisionan manualmente. Este modulo solo valida la sesion; no contiene
logica de negocio de suscripcion (eso vive en src/api/services).
"""


def require_login() -> bool:
    # TODO (Sprint 0/7): integrar streamlit-authenticator contra la tabla users.
    raise NotImplementedError("Pendiente: wiring de login.")
