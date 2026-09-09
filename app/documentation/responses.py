from app.schemas.errors.responses import ErrorResponseSchema

COMMON_RESPONSES = {
    422: {
        "model": ErrorResponseSchema,
        "description": "Los datos enviados no son válidos.",
    },
    500: {
        "model": ErrorResponseSchema,
        "description": "Se ha producido un error interno.",
    },
    503: {
        "model": ErrorResponseSchema,
        "description": "El servicio no se encuentra disponible temporalmente.",
    },
}


ORDER_RESPONSES = {
    **COMMON_RESPONSES,
    400: {
        "model": ErrorResponseSchema,
        "description": (
            "La petición es válida estructuralmente, pero no puede procesarse "
            "debido a un problema con los datos enviados."
        ),
        "content": {
            "application/json": {
                "examples": {
                    "uom_conversion_error": {
                        "summary": "Error en la conversión de unidades de medida",
                        "description": (
                            "La unidad de medida existe, pero no es posible realizar "
                            "la conversión necesaria para procesar la línea del pedido."
                        ),
                        "value": {
                            "error": {
                                "code": "UOM_CONVERSION_ERROR",
                                "message": (
                                    "Error en la conversión de unidades de medida."
                                ),
                                "details": {
                                    "referenciaUnidadMedida": "C6",
                                },
                            }
                        },
                    },
                }
            }
        },
    },
    404: {
        "model": ErrorResponseSchema,
        "description": (
            "No se ha encontrado alguno de los recursos necesarios "
            "para procesar el pedido."
        ),
        "content": {
            "application/json": {
                "examples": {
                    "product_not_found": {
                        "summary": "Producto no encontrado",
                        "description": (
                            "La referencia de producto indicada no existe " "en el ERP."
                        ),
                        "value": {
                            "error": {
                                "code": "PRODUCT_NOT_FOUND",
                                "message": "No existe el producto indicado.",
                                "details": {
                                    "referenciaProducto": "PEPITO",
                                },
                            }
                        },
                    },
                    "combination_not_found": {
                        "summary": "Combinación de producto no encontrada",
                        "description": (
                            "El artículo utiliza combinaciones, pero la combinación "
                            "indicada no existe."
                        ),
                        "value": {
                            "error": {
                                "code": "COMBINATION_NOT_FOUND",
                                "message": (
                                    "No existe la combinación de producto indicada."
                                ),
                                "details": {
                                    "referenciaCombinacion": "4115",
                                },
                            }
                        },
                    },
                    "uom_product_not_found": {
                        "summary": ("Unidad de medida no disponible para el artículo"),
                        "description": (
                            "La unidad de medida indicada no se encuentra configurada "
                            "para el artículo solicitado."
                        ),
                        "value": {
                            "error": {
                                "code": "UOM_PRODUCT_NOT_FOUND",
                                "message": (
                                    "No existe la unidad de medida indicada, "
                                    "para este artículo."
                                ),
                                "details": {
                                    "referenciaUnidadMedida": "C6",
                                },
                            }
                        },
                    },
                    "uom_not_found": {
                        "summary": "Unidad de medida no encontrada",
                        "description": (
                            "La referencia de unidad de medida indicada no existe "
                            "en el ERP."
                        ),
                        "value": {
                            "error": {
                                "code": "UOM_NOT_FOUND",
                                "message": ("No existe la unidad de medida indicada."),
                                "details": {
                                    "referenciaUnidadMedida": "KG",
                                },
                            }
                        },
                    },
                }
            }
        },
    },
    409: {
        "model": ErrorResponseSchema,
        "description": (
            "El recurso existe, pero su configuración actual impide "
            "procesar correctamente el pedido."
        ),
        "content": {
            "application/json": {
                "examples": {
                    "prices_and_cost_not_found": {
                        "summary": "Artículo sin precios ni costes",
                        "description": (
                            "El artículo existe, pero no dispone de información "
                            "de precios ni costes necesaria para crear la línea."
                        ),
                        "value": {
                            "error": {
                                "code": "PRICES_AND_COST_NOT_FOUND",
                                "message": (
                                    "No existen precios ni costes para "
                                    "el artículo indicado."
                                ),
                                "details": {
                                    "referenciaArticulo": "PEPITO",
                                },
                            }
                        },
                    },
                }
            }
        },
    },
}
