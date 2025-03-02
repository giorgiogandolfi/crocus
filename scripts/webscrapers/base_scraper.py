import glob
import json
import logging
import os
from abc import ABC, abstractmethod
from datetime import date

import requests
from pythonjsonlogger import jsonlogger
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BaseScraper(ABC):
    def __init__(
        self,
        provider_name: str,
        base_download_folder_path: str = None,
        is_headless: bool = False,
    ):
        if not base_download_folder_path:
            base_download_folder_path = (
                "/Users/giorgiogandolfi/development/etfs_downloads"
            )

        self.logger = self._initialize_classwide_logger()
        self.download_folder_path = self._generate_download_folder_path(
            base_download_folder_path, provider_name
        )
        self.products_json_path = f"{self.download_folder_path}/products.json"
        self.driver, self.wait = self._configure_driver(is_headless)

    def _initialize_classwide_logger(
        self,
        log_format: str = "%(asctime)s %(name)s %(levelname)s %(message)s",
        log_level: int = logging.INFO,
    ) -> logging.Logger:
        """
        Initiates the logger to a common standard
        """
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(log_level)
        handler = logging.StreamHandler()
        handler.setFormatter(jsonlogger.JsonFormatter(log_format))
        logger.addHandler(handler)

        return logger

    def _configure_driver(
        self,
        headless: bool = False,
    ) -> tuple[webdriver.Chrome, WebDriverWait]:
        """
        Configure the selenium WebDriver
        """
        self.logger.info("Configuring the WebDriver")
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")
        if self.download_folder_path:
            prefs = {"download.default_directory": self.download_folder_path}
            options.add_experimental_option("prefs", prefs)
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 20)

        return driver, wait

    def _generate_download_folder_path(self, base_path: str, provider_name: str) -> str:
        """
        Esures that the download folder path exists or else creates it
        The folder path returned will be like:
        /base_path/today_date/provider_name
        """
        today = date.today().strftime("%Y-%m-%d")
        dir_name = os.path.join(base_path, today, provider_name)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)

        return dir_name

    def _rename_latest_downloaded_file(self, new_file_name: str) -> bool:
        """
        Renames the most recently modified file in the download folder to new_file_name
        """
        files = glob.glob(os.path.join(self.download_folder_path, "*"))

        if not files:
            self.logger.error("No files found in the download folder")
            return False

        # Find latest and new files
        latest_file = max(files, key=os.path.getmtime)
        file_extension = latest_file.split(".")[-1]
        new_file_name = ".".join([new_file_name, file_extension])

        # Create the full path for the new file
        new_file_path = os.path.join(self.download_folder_path, new_file_name)

        try:
            self.logger.info(f"Renaming file {latest_file} to: {new_file_path}")
            os.rename(latest_file, new_file_path)
            return True
        except Exception as e:
            self.logger.error(f"Error renaming file {latest_file}: {e}")
            return False

    def quit(self) -> None:
        """
        Close the WebDriver
        """
        self.logger.info("Closing the WebDriver")
        self.driver.quit()

    def open_web_page(self, url: str) -> None:
        """
        Open a web page by its URL
        """
        self.logger.info(f"Opening web page: {url}")
        self.driver.get(url)

    def _click_button_by_xpath(self, xpath: str, btn_name: str = None) -> None:
        """
        Click a button given its xpath
        """
        self.logger.info(f"Clicking the {btn_name} button")
        try:
            button = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            button.click()
        except NoSuchElementException as e:
            self.logger.error(f"No {btn_name} button found: {e}")

    def _get_located_element(
        self, element_id: str, locator: str = "xpath"
    ) -> WebElement:
        """
        Get an element by its id
        """
        try:
            match locator:
                case "classname":
                    locator = By.CLASS_NAME
                case "xpath":
                    locator = By.XPATH
                case _:
                    self.logger.error(f"Locator not implemented: {locator}")
                    raise ValueError("Locator not implemented")

            web_element = self.wait.until(
                EC.presence_of_element_located(
                    (
                        locator,
                        element_id,
                    )
                )
            )
        except NoSuchElementException as e:
            self.logger.error(f"Element not found: {e}")

        return web_element

    def _write_products_json(self, products: dict) -> None:
        """
        Write the products dictionary into a JSON file
        """
        with open(self.products_json_path, "w") as json_file:
            json.dump(products, json_file, indent=4)

    def _read_products_json(self) -> dict:
        """
        Read the previously saved JSON file
        """
        with open(self.products_json_path, "r") as file:
            data = json.load(file)
            return data

    def _download_file_with_request(self, url: str, file_name: str) -> None:
        """
        Download a file from a URL using requests
        """
        self.logger.info(f"Downloading file from {url}")
        response = requests.get(url)
        if response.status_code == 200:
            file_path = os.path.join(self.download_folder_path, file_name)
            with open(file_path, "wb") as file:
                file.write(response.content)
        else:
            self.logger.error(f"Failed to download file: {response.status_code}")

    @abstractmethod
    def handle_initial_banners(self) -> None:
        """
        Handle the initial banners that appear when opening the website
        """
        pass

    @abstractmethod
    def get_products_json(self) -> None:
        """
        Get the products JSON from the website
        """
        pass

    @abstractmethod
    def download_product_files(self) -> None:
        """
        Download the product files from the website
        """
        pass
