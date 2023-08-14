import csv
import smtplib
from email.message import EmailMessage
from constants import (
    SMTP_SERVER,
    SMTP_PORT,
    GMAIL_USERNAME,
    GMAIL_PASSWORD,
)


def usd_to_number(usd_str: str):
    return int(usd_str.replace("$", "").replace(",", ""))


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
