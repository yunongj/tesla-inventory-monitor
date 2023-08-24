from enum import Enum


class ModelKey(Enum):
    MODEL_Y = "my"
    MODEL_3 = "m3"
    MODEL_X = "mx"
    MODEL_S = "ms"


class ModelName(Enum):
    MODEL_Y = "Model Y"
    MODEL_3 = "Model 3"
    MODEL_X = "Model X"
    MODEL_S = "Model S"


MODEL_KEY_NAME_MAP: dict[ModelKey, ModelName] = {
    ModelKey.MODEL_3: ModelName.MODEL_3,
    ModelKey.MODEL_Y: ModelName.MODEL_Y,
    ModelKey.MODEL_X: ModelName.MODEL_X,
    ModelKey.MODEL_S: ModelName.MODEL_S,
}

MODEL_NAME_KEY_MAP: dict[ModelName, ModelKey] = {
    v: k for k, v in MODEL_KEY_NAME_MAP.items()
}

BROWSER_PATH = "./chromedriver"
URL = "https://www.tesla.com/inventory/new/"
QUERY = "?arrangeby=plh&range=200&zip="

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
GMAIL_USERNAME = "117m4ojd@gmail.com"
GMAIL_PASSWORD = "xthjkgbpwrcczazs"

M3RWD = "Model 3 Rear-Wheel Drive"
MYAWD = "Model Y All-Wheel Drive"
LRAWD = "Long Range"
PAWD = "Performance"


DATA_ID_PREFIX: dict[ModelKey, str] = {
    ModelKey.MODEL_3: "5YJ3",
    ModelKey.MODEL_Y: "7SAY",
}

AREA_TO_ZIPCODE: dict[str, str] = {
    "Arizona": "85001",
    "Colorado": "80001",
    "Bay Area, CA": "94016",
    "Los Angeles, CA": "90001",
    "Florida": "33870",
    "Georgia": "31201",
    "Illinois": "60436",
    "Massachusetts": "02210",
    "Nevada": "89001",
    "New Jersey": "07001",
    "New York": "10001",
    "Ohio": "43001",
    "Oregon": "97001",
    "Texas": "77840",
    "Pennsylvania": "16823",
    "Washington": "98109",
    "Washington, DC": "20001",
}

ZIPCODE_TO_AREA: dict[str, str] = {v: k for k, v in AREA_TO_ZIPCODE.items()}

REFER_QUERY = "?referral=yunong861331"
