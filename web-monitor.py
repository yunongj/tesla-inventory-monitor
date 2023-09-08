import argparse
import asyncio
import random
import time
from datetime import datetime
from typing import List

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
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
) -> list[CarInfo]:
    driver.get(URL + model.value + QUERY + zip_code)
    try:
        result_container: WebElement = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.results-container--has-results")
            )
        )
        inventory_elements: List[WebElement] = result_container.find_elements(
            By.CSS_SELECTOR, "article.result.card"
        )
    except Exception as e:
        print("Failed to find inventory elements. Error: {}".format(e))
        return []

    cars: list[CarInfo] = []
    for item in inventory_elements:
        try:
            new_price = usd_to_number(
                item.find_element(By.CSS_SELECTOR, "span.result-purchase-price").text
            )
            old_price = usd_to_number(
                item.find_element(By.CSS_SELECTOR, "span.result-price-base-price").text
            )
        except NoSuchElementException:
            continue
        except Exception as e:
            print("Failed to find price element. Error: {}".format(e))
            continue
        data_id = item.get_attribute("data-id").split("-")[0]
        trim = item.find_element(By.CSS_SELECTOR, "div.result-basic-info div").text
        features = item.find_element(
            By.CSS_SELECTOR, "section.result-features.features-grid"
        ).text.replace("\n", " # ")
        cars.append(
            CarInfo(
                trim=trim,
                new_price=new_price,
                old_price=old_price,
                features=features,
                timestamp=datetime.now(),
                area=ZIPCODE_TO_AREA[zip_code],
                link=(
                    "https://www.tesla.com/"
                    + model.value
                    + "/order/"
                    + DATA_ID_PREFIX[model]
                    + data_id
                ),
                data_id=data_id,
            )
        )

    return cars


def filter_tesla_inventory(
    unfiltered_cars: list[CarInfo],
    condition: dict,
    existing_data_ids: set[str],
) -> list[CarInfo]:
    filtered_cars: list[CarInfo] = []
    for car in unfiltered_cars:
        if should_alert(
            int(condition["max_price"]),
            int(condition["min_discount"]),
            car.new_price,
            car.old_price,
        ) and (not car.data_id in existing_data_ids):
            if len(condition["trims"]) > 0:
                eligible = False
                for trim in condition["trims"]:
                    if trim in car.trim:
                        eligible = True
                        break
                if not eligible:
                    continue

            # if len(condition["features"]) > 0:
            #     eligible = True
            #     for feature in condition["features"]:
            #         if feature not in features_element.text:
            #             eligible = False
            #             break
            #     if not eligible:
            #         continue

            filtered_cars.append(car)

    return filtered_cars


async def main():
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
            existing_data_ids = get_data_ids_in_gs()
            new_data_ids = set()
            gs_data_to_write = []

            loop = asyncio.get_event_loop()
            futures = []

            for (zip_code, model), conditions in clients.items():
                unfiltered_cars = get_tesla_inventory_info(zip_code, model, driver)
                for condition in conditions:
                    filtered_cars: list[CarInfo] = filter_tesla_inventory(
                        unfiltered_cars,
                        condition,
                        existing_data_ids,
                    )
                    if len(filtered_cars) > 0:
                        email_subject = (
                            "Tesla Availability Alert | "
                            + MODEL_KEY_NAME_MAP[model].value
                            + " | "
                            + ZIPCODE_TO_AREA[zip_code]
                        )
                        email_address = condition["email"]
                        email_body = ("\n\n\n").join(
                            [
                                format_email_content(car, condition["refer"])
                                for car in filtered_cars
                            ]
                        )

                        futures.append(
                            loop.run_in_executor(
                                None,
                                send_email,
                                email_subject,
                                email_address,
                                email_body,
                            )
                        )

                        # Add cars to be appended to google sheet
                        for car in filtered_cars:
                            if car.data_id not in new_data_ids:
                                new_data_ids.add(car.data_id)
                                gs_data_to_write.append(car.to_gs_row())

            if len(gs_data_to_write) > 0:
                print(gs_data_to_write)
                if args.playsound:
                    from playsound import playsound

                    playsound("./alert.mp3")
                write_to_gs(gs_data_to_write)

            driver.quit()
            await asyncio.gather(*futures)
            time.sleep(random.randint(30, 60))

        except KeyboardInterrupt:
            print("Quitting driver...")
            driver.quit()
            break
        except Exception as e:
            print("Error: {}".format(e))
            time.sleep(random.randint(30, 60))


if __name__ == "__main__":
    asyncio.run(main())
