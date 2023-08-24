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

PRICE_SHEET_KEY = "1OqP3qCCKYXuqvIhWLQY_4KwrdAMCVaKbD4iixHC7JLQ"
INPUT_SHEET_KEY = {
    "prod": "1GYcPORDUroIQIOfYDwmpxDIMgHDtiRe_Hj3MaaUvHis",
    "test": "128Pa9dxqnQFX97H2Vod1fL132AIP3-f5pmRQl3E5-ZY",
}
