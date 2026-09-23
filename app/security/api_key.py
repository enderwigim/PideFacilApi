# API Key Generation
import hashlib
import hmac
import secrets
from dataclasses import dataclass


@dataclass(frozen=True)
class GeneratedAPIKey:
    s_api_key: str
    s_secret: str


def generate_api_key() -> GeneratedAPIKey:
    s_api_key: str
    s_secret: str
    generated_api: GeneratedAPIKey

    # Generamos el secret
    s_secret = secrets.token_urlsafe(16)  # Genera de 32 caracteres.
    # Generamos la api_key
    s_api_key = secrets.token_urlsafe(16)

    generated_api = GeneratedAPIKey(s_api_key=s_api_key, s_secret=s_secret)
    return generated_api


def get_signature(s_api_key, s_timestamp, s_secret) -> str:
    # Construimos el mensaje que vamos a firmar.
    s_message = s_api_key + "\n" + s_timestamp

    # Generamos la firma utilizando el Secret.
    s_signature = hmac.new(
        key=s_secret.encode("utf-8"),
        msg=s_message.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    return s_signature

    # 2026-09-22 Santi. Obsoleto.
    # # Identificador interno de la credencial.
    # key_id = uuid.uuid4()
    # # Identificador público.
    # key_prefix = f"{key_id.hex}"  # hex is the UUID as a 32-character hexadecimal string
    # # Parte secreta.
    # secret = secrets.token_urlsafe(32)

    # # Credencial completa que entregaremos al cliente.
    # api_key = f"{key_prefix}_{secret}"

    # # Hash de la parte secreta.
    # key_hash = hashlib.sha256(secret.encode("utf-8")).hexdigest()

    # return GeneratedAPIKey(
    #     key_id=key_id,
    #     key_prefix=key_prefix,
    #     key_hash=key_hash,
    #     api_key=api_key,
    # )


# 2026-09-22 Obsoleto.
# def parse_api_key(api_key: str) -> tuple[str, str] | None:

#     # Formato esperado:
#     # UUID_HEX_SECRETO
#     #   Cada uno está compuesto por:
#     # UUID_HEX: 32 caracteres hexadecimales. Este nos servirá para identificarlo por base de datos.
#     # SECRETO: 43 caracteres generados con

#     # Si recibimos un api_key con ese formato. Lo separamos, devolviendo un tuple con el prefijo y el secreto.
#     match = re.fullmatch(
#         r"([0-9a-f]{32})_([A-Za-z0-9_-]{43})",
#         api_key,
#     )

#     if match is None:
#         return None

#     key_prefix = match.group(1)
#     secret = match.group(2)

#     return key_prefix, secret
