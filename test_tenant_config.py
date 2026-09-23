import hashlib
import hmac
from datetime import datetime, timezone

import requests

# -------------------------------------------
# CONFIGURACIÓN DE LA PRUEBA
# -------------------------------------------

API_URL = "http://cliente-a.apiiqs.local:8000/v1/products"

# Credenciales generadas para cliente-a.
# Completar con los valores reales.
API_KEY = "7U4v7mlA5T8hFcTguRAnHg"

SECRET = "4igg3g94Y4B8MZeV2AnLsQ"


# -------------------------------------------
# 1. GENERAR TIMESTAMP EN UTC
# -------------------------------------------

timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# -------------------------------------------
# 2. GENERAR FIRMA HMAC-SHA256
# -------------------------------------------

# Debe coincidir con el mensaje firmado
# por tu función get_signature().

message = API_KEY + "\n" + timestamp

signature = hmac.new(
    key=SECRET.encode("utf-8"),
    msg=message.encode("utf-8"),
    digestmod=hashlib.sha256,
).hexdigest()


# -------------------------------------------
# 3. PREPARAR CABECERAS HTTP
# -------------------------------------------

headers = {
    "X-API-Key": API_KEY,
    "X-Timestamp": timestamp,
    "X-Signature": signature,
}


# -------------------------------------------
# 4. REALIZAR PETICIÓN A FASTAPI
# -------------------------------------------

response = requests.get(
    API_URL,
    headers=headers,
    timeout=15,
)


# -------------------------------------------
# 5. MOSTRAR RESULTADO
# -------------------------------------------

print("\n--- PRUEBA DE AUTENTICACIÓN ---")

print("API_Key:", API_KEY)
print("Timestamp:", timestamp)
print("Signature:", signature)
print("HTTP Status:", response.status_code)

# print("Respuesta:")
# print(response.text)
