import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)
from sqlalchemy.types import DateTime


class ConfigBase(DeclarativeBase):
    pass


class TenantModel(ConfigBase):

    __tablename__ = "TENANT_TEN"

    ten_id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    ten_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    ten_hostname: Mapped[str] = mapped_column(
        String(253),
        unique=True,
        nullable=False,
    )

    ten_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )

    ten_created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class TenantDatabaseModel(ConfigBase):

    __tablename__ = "TENANTDATABASE_TDB"

    ten_tdb_fk: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("TENANT_TEN.ten_id"),
        primary_key=True,
    )

    tdb_host: Mapped[str] = mapped_column(
        String(253),
        nullable=False,
    )

    tdb_port: Mapped[int] = mapped_column(
        Integer,
        default=5432,
        server_default="5432",
        nullable=False,
    )

    tdb_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    tdb_username: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    tdb_password_secret: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    tdb_sslmode: Mapped[str] = mapped_column(
        String(30),
        default="verify-full",
        server_default="verify-full",
        nullable=False,
    )

    tdb_sslrootcert: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )


class TenantAPIKeyModel(ConfigBase):

    __tablename__ = "TENANTAPIKEY_TAK"

    __table_args__ = (
        CheckConstraint(
            "tak_expires_at IS NULL " "OR tak_expires_at > tak_created_at",
            name="chk_api_key_expiration",
        ),
        CheckConstraint(
            "tak_revoked_at IS NULL " "OR tak_enabled = FALSE",
            name="chk_api_key_revocation",
        ),
    )

    tak_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    ten_tak_fk: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("TENANT_TEN.ten_id"),
        nullable=False,
    )

    tak_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    tak_key_prefix: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
    )

    tak_key_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    tak_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )

    tak_created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    tak_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    tak_last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    tak_revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
