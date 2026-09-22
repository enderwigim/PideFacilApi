import hashlib

# Ajustar las rutas si tus archivos tienen
# nombres diferentes.


def test_api_key_validation():

    test = hashlib.sha256(b"abc").hexdigest()
    print(test)


if __name__ == "__main__":
    test_api_key_validation()
