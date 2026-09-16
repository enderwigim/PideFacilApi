from threading import Lock

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.core.tenancy.configuration import TenantConfiguration


class TenantConnectionManager:
    def __init__(self):
        # La idea es mantener un único unico engine por cliente, cosa de que exista mientras se sigan creando consultas. De esta manera se evita
        # estar todo el tiempo creando conexiones nuevas.
        self._engines: dict[str, Engine] = {}
        self._session_makers: dict[str, sessionmaker] = {}
        self._lock = Lock()

    def get_session_maker(
        self,
        configuration: TenantConfiguration,
    ) -> sessionmaker:

        tenant_id = configuration.tenant_id

        # 2026-09-16
        # Realizamos un lock. Esto lo que hace es evitar que un segundo hilo ejecutandose pase por aquí
        # y me vuelva a crear la sesión. Lo que hacemos es bloquear este trozo, cuando llegue un segundo hilo se queda esperando.
        # Cuando se termina de crear la conexión, valida si existe o no.
        with self._lock:
            if tenant_id not in self._session_makers:
                self._create_connection(configuration)

        return self._session_makers[tenant_id]

    def _create_connection(
        self,
        configuration: TenantConfiguration,
    ) -> None:

        database_config = configuration.database
        # Creamos el engine y la sesión.
        engine = create_engine(
            database_config.database_url,
            pool_pre_ping=database_config.pool_pre_ping,
            echo=database_config.echo,
        )

        session_maker = sessionmaker(
            bind=engine,
            autoflush=False,
            autocommit=False,
        )
        # Las agregamos a nuestro dic de engines y session.
        self._engines[configuration.tenant_id] = engine
        self._session_makers[configuration.tenant_id] = session_maker

    # Eliminamos el engine creado.
    def dispose_tenant(self, tenant_id: str) -> None:
        engine = self._engines.pop(tenant_id, None)

        self._session_makers.pop(tenant_id, None)

        if engine is not None:
            engine.dispose()


tenant_connection_manager = TenantConnectionManager()
