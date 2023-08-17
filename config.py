from constants import *

CLIENTS = [
    {
        "zip_code": "95050",
        "model": ModelKey.MODEL_Y,
        "conditions": [
            {
                "email": "jiangyntz@gmail.com",
                "max_price": 1000000,
                "min_discount": 1000,
                "trims": [MYAWD, LRAWD],
                "features": [],
            },
        ],
    },
]

REFRESH_INTERVAL = 150  # in seconds
