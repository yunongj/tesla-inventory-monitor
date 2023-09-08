import csv
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage

import gspread
from gspread.worksheet import Worksheet
from oauth2client.service_account import ServiceAccountCredentials
from config import PRICE_SHEET_KEY

from constants import *
from type import CarInfo


def usd_to_number(usd_str: str):
    return int(usd_str.replace("$", "").replace(",", ""))


def number_to_usd(number: float):
    return f"${number:,}"


def write_to_csv(data: list, filename: str = "prices.csv"):
    with open(
        filename, "a", newline=""
    ) as file:  # 'a' stands for 'append', so you don't overwrite previous data.
        writer = csv.writer(file)
        writer.writerow(data)


def data_in_csv(data_id: str, filename: str = "prices.csv"):
    with open(filename, "r") as file:
        reader = csv.reader(file)
        for row in reader:
            if row[-1] == data_id:
                return True

    return False


def write_to_gs(
    data: list[list],
    key: str = PRICE_SHEET_KEY,
    sheet: str = "prices",
):
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "./keys/google-sheets-key.json", scope
    )
    client = gspread.authorize(creds)

    sheet: Worksheet = client.open_by_key(key).worksheet(sheet)
    sheet.append_rows(data)


def get_data_ids_in_gs(
    key: str = PRICE_SHEET_KEY,
    sheet_name: str = "prices",
) -> set[str]:
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "./keys/google-sheets-key.json", scope
    )
    client = gspread.authorize(creds)

    sheet: Worksheet = client.open_by_key(key).worksheet(sheet_name)
    data_ids: list[str] = sheet.col_values(9)[1:]
    # found_times: list[str] = sheet.col_values(6)[1:]

    # recent_data_ids = set()
    # for i in range(len(data_ids)):
    #     if datetime.now() - datetime.strptime(
    #         found_times[i], "%m/%d/%Y, %H:%M:%S %Z"
    #     ) < timedelta(hours=12):
    #         recent_data_ids.add(data_ids[i])

    # return recent_data_ids
    return data_ids


def get_trim(model: ModelKey, trim: str) -> str:
    if trim == "Standard Range":
        if model == ModelKey.MODEL_3:
            return M3RWD
        elif model == ModelKey.MODEL_Y:
            return MYAWD
    else:
        return trim


def get_user_input_from_gs(
    key: str,
    sheet_name: str = "Form Responses 1",
):
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "./keys/google-sheets-key.json", scope
    )
    client = gspread.authorize(creds)

    sheet: Worksheet = client.open_by_key(key).worksheet(sheet_name)
    inputs: list[list[str]] = sheet.get_values()

    clients: dict[tuple[str, ModelKey], list[dict]] = {}

    for input in inputs[1:]:
        if "paid" not in input[9]:
            continue

        # print("checking for customer: " + input[1])

        zip_code = AREA_TO_ZIPCODE[input[2]]
        model = MODEL_NAME_KEY_MAP[ModelName(input[3])]
        if (zip_code, model) not in clients:
            clients[(zip_code, model)] = []
        clients[(zip_code, model)].append(
            {
                "timestamp": input[0],
                "email": input[1],
                "max_price": input[4] or "1000000",
                "min_discount": input[5] or "1000",
                "trims": [
                    get_trim(model, trim.strip()) for trim in input[6].split(",")
                ],
                "refer": True if "A" in input[7] else False,
            }
        )

    # print(clients)

    return clients


def send_email(subject, to, body):
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(GMAIL_USERNAME, GMAIL_PASSWORD)

        msg = EmailMessage()
        msg.set_content(body, charset="utf-8")
        msg["Subject"] = subject
        msg["From"] = GMAIL_USERNAME
        msg["To"] = to

        smtp.send_message(msg)
        smtp.close()


def should_alert(max_price: int, min_discount: int, new_price: int, old_price: int):
    return new_price <= max_price and (old_price - new_price) >= min_discount


def format_email_content(car_info: CarInfo, refer: bool) -> str:
    purchase_link = car_info.link
    if refer:
        purchase_link += REFER_QUERY

    return f"""Model: {car_info.trim}
New Price: {number_to_usd(car_info.new_price)}
Old Price: {number_to_usd(car_info.old_price)}
Discount: {number_to_usd(car_info.discount)}
Features: {car_info.features}
Area: {car_info.area}
Purchase Link: {purchase_link}"""
