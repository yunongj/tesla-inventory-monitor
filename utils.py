import csv
import smtplib
from email.message import EmailMessage

import gspread
from gspread.worksheet import Worksheet
from oauth2client.service_account import ServiceAccountCredentials

from constants import *


def usd_to_number(usd_str: str):
    return float(usd_str.replace("$", "").replace(",", ""))


def number_to_usd(number: float):
    return f"${number:,.2f}"


def calculate_discount(old_price: str, new_price: str) -> str:
    """Compute the discount amount and percentage based on old and new prices."""

    old = usd_to_number(old_price)
    new = usd_to_number(new_price)

    return number_to_usd(old - new)


def write_to_csv(data: list, filename: str = "prices.csv"):
    """
    Write the given data into a specified CSV file.

    Args:
    - data (list): The data to write to the file. Each item in the list should be a tuple or list representing a row.
    - filename (str): The name of the file to write to. Default is "found_items.csv".
    """
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
    data: list,
    key: str = "1OqP3qCCKYXuqvIhWLQY_4KwrdAMCVaKbD4iixHC7JLQ",
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
    sheet.append_row(data)


def data_in_gs(
    data_id: str,
    key: str = "1OqP3qCCKYXuqvIhWLQY_4KwrdAMCVaKbD4iixHC7JLQ",
    sheet_name: str = "prices",
):
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "./keys/google-sheets-key.json", scope
    )
    client = gspread.authorize(creds)

    sheet: Worksheet = client.open_by_key(key).worksheet(sheet_name)
    data_ids: list[str] = sheet.col_values(9)

    for id in data_ids:
        if id == data_id:
            return True

    return False


def get_trim(model: ModelKey, trim: str) -> str:
    if trim == "Standard Range":
        if model == ModelKey.MODEL_3:
            return M3RWD
        elif model == ModelKey.MODEL_Y:
            return MYAWD
    else:
        return trim


def get_user_input_from_gs(
    key: str = "1GYcPORDUroIQIOfYDwmpxDIMgHDtiRe_Hj3MaaUvHis",
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
        if "paid" not in input[8]:
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
                "max_price": input[4],
                "min_discount": input[5],
                "trims": [
                    get_trim(model, trim.strip()) for trim in input[6].split(",")
                ],
            }
        )

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


def should_alert(max_price: int, min_discount: int, new_price: int, base_price: int):
    return new_price <= max_price and (base_price - new_price) >= min_discount
