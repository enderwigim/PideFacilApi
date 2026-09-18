from datetime import datetime, now, timedelta
from threading import Lock

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker

from app.core.tenancy.configuration import TenantConfiguration
from app.db.tables import TABLES
from app.db.tenant_database_context import TenantDatabaseContext
from app.db.tenant_models import create_tenant_models


# 2026-09-16 Cada tenant tendrá un contexto propio.
# El contexto incluirá Engine + SessionMaker + Base + Models
class TenantConnectionManager:
    def __init__(self):
        # Engine + SessionMaker + Base + Models
        self._contexts: dict[str, TenantDatabaseContext] = {}
        self._lock = Lock()

    def get_context(
        self,
        configuration: TenantConfiguration,
    ) -> TenantDatabaseContext:
        dt_current_version: datetime
        n_minutes_validate: int
        context: TenantDatabaseContext
        old_context: TenantDatabaseContext

        n_minutes_validate = 5
        # A través del tenant obtenemos el id.
        tenant_id = configuration.tenant_id

        # Si no existe un contexto, lo creamos.
        context = self._contexts.get(tenant_id)
        # Hacemos una doble validación, porque la idea es realizar un bloqueo si el contexto no existe.
        # Si no existe el contexto, bloqueo. Y no bloqueo a todas las request.
        # Por ejemplo, contexto de cliente A existe. Pasa, porque el bloqueo de hilo es más adelante. No espera a la creación de cliente B.
        # Si es cliente B y llegó antes de la creada del contexto. Se queda bloqueado esperando, pero luego vuelve a revisar si se creó.
        # Evitando la creación de este segundo contexto.
        if context is None:
            with self._lock:
                context = self._contexts.get(tenant_id)
                if context is None:
                    context = self._create_context(configuration)

                    self._contexts[tenant_id] = context
        else:
            if now() - context.last_version_check >= timedelta(
                minutes=n_minutes_validate
            ):
                context.last_version_check = now()

                dt_current_version = self._get_analysis_version(context.engine)
                if context.analysis_version != dt_current_version:
                    # Almacenamos el contexto antiguo antes de intentar crear uno nuevo.
                    old_context = context

                    # Creamos el nuevo contexto.
                    context = self._create_context(configuration)

                    # Reemplazamos el contexto anterior con el nuevo.
                    self._contexts[tenant_id] = context
                    # Nos deshacemos del anterior.
                    old_context.engine.dispose()

        return context

    # Función privada para la creación del contexto.
    def _create_context(
        self,
        configuration: TenantConfiguration,
    ) -> TenantDatabaseContext:
        n_current_db_analysis: int
        dt_creation_time: datetime

        database_config = configuration.database

        # Engine propio del tenant
        engine = create_engine(
            database_config.database_url,
            pool_pre_ping=database_config.pool_pre_ping,
            echo=database_config.echo,
        )

        n_current_db_analysis = self._get_analysis_version(engine)

        print(n_current_db_analysis)
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

            dt_creation_time = now()
            # Devolvemos todo el contexto.
            return TenantDatabaseContext(
                engine=engine,
                session_maker=session_maker,
                base=base,
                models=models,
                analysis_version=n_current_db_analysis,
                last_version_check=dt_creation_time,
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

    def _get_analysis_version(self, engine: Engine):
        with engine.connect() as connection:
            result = connection.execute(text("""
                    SELECT ver_analysis
                    FROM "VERSION_VER"
                    LIMIT 1
                    """))

        return result.scalar_one()


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
