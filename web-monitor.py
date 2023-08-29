import argparse
import random
import time
from datetime import datetime
from typing import List

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import *
from constants import *
from type import CarInfo
from utils import *


def get_tesla_inventory_info(
    zip_code: str, model: ModelKey, driver: WebDriver
) -> List[WebElement]:
    driver.get(URL + model.value + QUERY + zip_code)

    try:
        result_container: WebElement = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.results-container--has-results")
            )
        )
        # Find the element(s) - Adjust the method to fit the actual webpage structure
        inventory_elements: List[WebElement] = result_container.find_elements(
            By.CSS_SELECTOR, "article.result.card"
        )
    except Exception as e:
        print("Failed to find inventory elements. Error: {}".format(e))
        return []

    return inventory_elements


def filter_tesla_inventory(
    inventory_elements: List[WebElement],
    condition: dict,
    model: ModelKey,
    zip_code: str,
    existing_data_ids: set[str],
) -> list[CarInfo]:
    cars = []

    for item in inventory_elements:
        new_price = usd_to_number(
            item.find_element(By.CSS_SELECTOR, "span.result-purchase-price").text
        )
        old_price = usd_to_number(
            item.find_element(By.CSS_SELECTOR, "span.result-price-base-price").text
        )
        data_id = item.get_attribute("data-id").split("-")[0]

        if should_alert(
            int(condition["max_price"]),
            int(condition["min_discount"]),
            new_price,
            old_price,
        ) and (not data_id in existing_data_ids):
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

            car_info = CarInfo(
                model_element.text,
                new_price,
                old_price,
                features_element.text.replace("\n", " # "),
                datetime.now(),
                ZIPCODE_TO_AREA[zip_code],
                (
                    "https://www.tesla.com/"
                    + model.value
                    + "/order/"
                    + DATA_ID_PREFIX[model]
                    + data_id
                ),
                data_id,
            )
            cars.append(car_info)

    return cars


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--playsound", action="store_true", help="Plays a sound when deal is found"
    )
    parser.add_argument("--test", action="store_true", help="Enable test mode")
    args = parser.parse_args()

    mode = "test" if args.test else "prod"

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )

    while True:
        try:
            driver = webdriver.Chrome(options)
            clients = get_user_input_from_gs(INPUT_SHEET_KEY[mode])
            existing_data_ids = set(get_data_ids_in_gs())
            new_data_ids = set()
            gs_data_to_write = []

            for (zip_code, model), conditions in clients.items():
                inventory_elements = get_tesla_inventory_info(zip_code, model, driver)
                for condition in conditions:
                    cars = filter_tesla_inventory(
                        inventory_elements,
                        condition,
                        model,
                        zip_code,
                        existing_data_ids,
                    )
                    if len(cars) > 0:
                        send_email(
                            "Tesla Availability Alert | "
                            + MODEL_KEY_NAME_MAP[model].value
                            + " | "
                            + ZIPCODE_TO_AREA[zip_code],
                            condition["email"],
                            ("\n\n\n").join(
                                [
                                    format_email_content(car_info, condition["refer"])
                                    for car_info in cars
                                ]
                            ),
                        )

                        for car in cars:
                            if car.data_id not in new_data_ids:
                                new_data_ids.add(car.data_id)
                                gs_data_to_write.append(car.to_gs_row())

                        if args.playsound:
                            from playsound import playsound

                            playsound("./alert.mp3")

            if len(gs_data_to_write) > 0:
                write_to_gs(gs_data_to_write)

            driver.quit()
            time.sleep(random.randint(30, 60))

        except KeyboardInterrupt:
            print("Quitting driver...")
            driver.quit()
            break
        except Exception as e:
            print("Error: {}".format(e))
            time.sleep(random.randint(30, 60))
