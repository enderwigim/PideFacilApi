from threading import Lock

from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker

from app.core.tenancy.configuration import TenantConfiguration
from app.db.tables import TABLES
from app.db.tenant_database_context import TenantDatabaseContext
from app.db.tenant_models import create_tenant_models


# 2026-09-16 Cada tenant tendrá un contexto propio.
class TenantConnectionManager:
    def __init__(self):
        # Cada tenant tendrá su propio contexto:
        # Engine + SessionMaker + Base + Models
        self._contexts: dict[str, TenantDatabaseContext] = {}
        self._lock = Lock()

    def get_context(
        self,
        configuration: TenantConfiguration,
    ) -> TenantDatabaseContext:
        # A través del tenant obtenemos el id.
        tenant_id = configuration.tenant_id

        # Si no existe un contexto, lo creamos.
        with self._lock:
            context = self._contexts.get(tenant_id)
            if context is None:
                context = self._create_context(configuration)

                self._contexts[tenant_id] = context

            return context

    # Función privada para la creación del contexto.
    def _create_context(
        self,
        configuration: TenantConfiguration,
    ) -> TenantDatabaseContext:

        database_config = configuration.database

        # Engine propio del tenant
        engine = create_engine(
            database_config.database_url,
            pool_pre_ping=database_config.pool_pre_ping,
            echo=database_config.echo,
        )

        try:
            # Metadata propia del tenant
            metadata = MetaData()

            # Leemos únicamente las tablas de Integra
            # que utiliza nuestra API.
            metadata.reflect(
                bind=engine,
                only=TABLES,
            )

            # Creamos un Base independiente para este tenant.
            base = automap_base(
                metadata=metadata,
            )

            base.prepare(
                generate_relationship=lambda *args, **kwargs: None,
            )

            # Obtenemos las referencias a los modelos.
            models = create_tenant_models(base)

            # SessionMaker asociado exclusivamente
            # al Engine de este tenant.
            session_maker = sessionmaker(
                bind=engine,
                autoflush=False,
                autocommit=False,
            )

            # Devolvemos todo el contexto.
            return TenantDatabaseContext(
                engine=engine,
                session_maker=session_maker,
                base=base,
                models=models,
            )

        except Exception:
            # Si falla el reflect/automap,
            # descartamos el Engine creado.
            engine.dispose()
            raise

    def dispose_tenant(
        self,
        tenant_id: str,
    ) -> None:

        with self._lock:
            context = self._contexts.pop(
                tenant_id,
                None,
            )
            if context is not None:
                context.engine.dispose()


tenant_connection_manager = TenantConnectionManager()

# class TenantConnectionManager:
#     def __init__(self):
#         # La idea es mantener un único unico engine por cliente, cosa de que exista mientras se sigan creando consultas. De esta manera se evita
#         # estar todo el tiempo creando conexiones nuevas.
#         self._engines: dict[str, Engine] = {}
#         self._session_makers: dict[str, sessionmaker] = {}
#         self._lock = Lock()

#     def get_session_maker(
#         self,
#         configuration: TenantConfiguration,
#     ) -> sessionmaker:

#         tenant_id = configuration.tenant_id

#         # 2026-09-16
#         # Realizamos un lock. Esto lo que hace es evitar que un segundo hilo ejecutandose pase por aquí
#         # y me vuelva a crear la sesión. Lo que hacemos es bloquear este trozo, cuando llegue un segundo hilo se queda esperando.
#         # Cuando se termina de crear la conexión, valida si existe o no.
#         with self._lock:
#             if tenant_id not in self._session_makers:
#                 self._create_connection(configuration)

#         return self._session_makers[tenant_id]

#     def _create_connection(
#         self,
#         configuration: TenantConfiguration,
#     ) -> None:

#         database_config = configuration.database
#         # Creamos el engine y la sesión.
#         engine = create_engine(
#             database_config.database_url,
#             pool_pre_ping=database_config.pool_pre_ping,
#             echo=database_config.echo,
#         )

#         session_maker = sessionmaker(
#             bind=engine,
#             autoflush=False,
#             autocommit=False,
#         )
#         # Las agregamos a nuestro dic de engines y session.
#         self._engines[configuration.tenant_id] = engine
#         self._session_makers[configuration.tenant_id] = session_maker

#     # Eliminamos el engine creado.
#     def dispose_tenant(self, tenant_id: str) -> None:
#         engine = self._engines.pop(tenant_id, None)

#         self._session_makers.pop(tenant_id, None)

#         if engine is not None:
#             engine.dispose()


# tenant_connection_manager = TenantConnectionManager()
