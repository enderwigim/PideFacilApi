# API Key Generation
import hashlib
import hmac
import secrets
import uuid
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


@dataclass(frozen=True)
class GeneratedAPIKey:
    key_id: uuid.UUID
    key_prefix: str
    key_hash: str
    api_key: str


def generate_api_key() -> GeneratedAPIKey:
    # Identificador interno de la credencial.
    key_id = uuid.uuid4()
    # Identificador público.
    key_prefix = f"{key_id.hex}"  # hex is the UUID as a 32-character hexadecimal string
    # Parte secreta.
    secret = secrets.token_urlsafe(32)

    # Credencial completa que entregaremos al cliente.
    api_key = f"{key_prefix}_{secret}"

    # Hash de la parte secreta.
    key_hash = hashlib.sha256(secret.encode("utf-8")).hexdigest()

    return GeneratedAPIKey(
        key_id=key_id,
        key_prefix=key_prefix,
        key_hash=key_hash,
        api_key=api_key,
    )


def verify_api_key(
    secret: str,
    stored_hash: str,
) -> bool:
    calculated_hash = hashlib.sha256(secret.encode("utf-8")).hexdigest()

    return hmac.compare_digest(
        calculated_hash,
        stored_hash,
    )


async def get_authenticated_tenant(
    api_key: str | None = Depends(api_key_header),
):
    # 1. Comprobar que se ha enviado una API Key.
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="API_KEY_REQUIRED"
        )

    # 2. Identificar la credencial y verificar
    #    criptográficamente su parte secreta.

    # 3. Comprobar que la credencial está activa
    #    y que no ha caducado.

    # 4. Obtener el Tenant al que pertenece.

    # 5. Comprobar que el Tenant está activo.

    # 6. Comprobar que el Tenant coincide
    #    con el subdominio solicitado.

    # 7. Devolver el contexto del Tenant
    #    autenticado.
