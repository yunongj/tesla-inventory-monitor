import argparse
import time
from datetime import datetime
from typing import List

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from config import *
from constants import *
from utils import *


def get_tesla_inventory_info(
    zip_code: str, model: ModelKey, driver: WebDriver
) -> List[WebElement]:
    driver.get(URL + model.value + QUERY + zip_code)
    time.sleep(5)  # Let the page load

    # Find the element(s) - Adjust the method to fit the actual webpage structure
    inventory_elements = driver.find_elements(By.CSS_SELECTOR, "article.result.card")

    return inventory_elements


def filter_tesla_inventory(
    inventory_elements: List[WebElement],
    condition: dict,
    model: ModelKey,
    zip_code: str,
):
    info_strs = []

    for item in inventory_elements:
        new_price_element = item.find_element(
            By.CSS_SELECTOR, "span.result-purchase-price"
        )
        base_price_element = item.find_element(
            By.CSS_SELECTOR, "span.result-price-base-price"
        )
        data_id = item.get_attribute("data-id").split("-")[0]

        if should_alert(
            int(condition["max_price"]),
            int(condition["min_discount"]),
            usd_to_number(new_price_element.text),
            usd_to_number(base_price_element.text),
        ) and not data_in_gs(data_id):
            model_element = item.find_element(
                By.CSS_SELECTOR, "div.result-basic-info div"
            )
            if len(condition["trims"]) > 0:
                eligible = False
                for trim in condition["trims"]:
                    if trim in model_element.text:
                        eligible = True
                        break
                if not eligible:
                    continue

            features_element = item.find_element(
                By.CSS_SELECTOR, "section.result-features.features-grid"
            )

            # if len(condition["features"]) > 0:
            #     eligible = True
            #     for feature in condition["features"]:
            #         if feature not in features_element.text:
            #             eligible = False
            #             break
            #     if not eligible:
            #         continue

            info_list = [
                model_element.text,
                new_price_element.text,
                base_price_element.text,
                calculate_discount(
                    old_price=base_price_element.text, new_price=new_price_element.text
                ),
                features_element.text.replace("\n", " # "),
                datetime.now().strftime("%m/%d/%Y, %H:%M:%S") + " PST",
                zip_code,
                "https://www.tesla.com/"
                + model.value
                + "/order/"
                + DATA_ID_PREFIX[model]
                + data_id,
                data_id,
            ]
            write_to_gs(info_list)

            info_str = (" | ").join(info_list)
            info_strs.append(info_str)

    return info_strs


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--playsound", action="store_true", help="Plays a sound when deal is found"
    )
    args = parser.parse_args()

    while True:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        driver = webdriver.Chrome(options)

        clients = get_user_input_from_gs()

        for (zip_code, model), conditions in clients.items():
            inventory_elements = get_tesla_inventory_info(zip_code, model, driver)
            for condition in conditions:
                info_strs = filter_tesla_inventory(
                    inventory_elements,
                    condition,
                    model,
                    zip_code,
                )
                if len(info_strs) > 0:
                    # print(info_strs)
                    send_email(
                        "Tesla Availability Alert "
                        + MODEL_KEY_NAME_MAP[model].value
                        + " "
                        + zip_code,
                        condition["email"],
                        ("\n\n\n").join(info_strs),
                    )

                    if args.playsound:
                        from playsound import playsound

                        playsound("./alert.mp3")

        driver.quit()
        time.sleep(REFRESH_INTERVAL)
