import logging
import os
from abc import ABC, abstractmethod
from datetime import date
from time import sleep

from pythonjsonlogger import jsonlogger

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from .web_drivers import LocalFirefoxDriver, RemoteFirefoxWebDriver
from .utils import (
    create_folder,
    download_file_with_request,
    read_json,
    rename_latest_file_in_folder,
    write_json,
)


class BaseScraper(ABC):
    def __init__(
        self,
        provider_name: str,
        base_path: str = "/app/raw-files",
        # base_path: str = "/Users/giorgiogandolfi/development/etfs_downloads",
    ):
        self.logger = self._initialize_classwide_logger()
        # There will be two download folders:
        # the first one will be the one where the selenium browser downloads the files;
        # the second one will be basd also on today's date and the provider name.
        # Generate the download folder path, create the folder if id doesn't exist
        self.base_path = base_path
        self.full_path = self._generate_full_path(self.base_path, provider_name)
        # self.full_path = base_path
        self.products_file = os.path.join(self.full_path, "products.json")
        webdriver = RemoteFirefoxWebDriver(self.full_path)
        self.driver = webdriver.get_driver()
        self.driver.set_window_size(1920, 1080)
        self.wait = webdriver.get_wait()

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

    def _generate_full_path(self, base_path: str, provider_name: str) -> str:
        """
        Esures that the download folder path exists or else creates it
        The folder path returned will be like:
        /base_path/today_date/provider_name
        """
        today = date.today().strftime("%Y-%m-%d")
        dir_name = os.path.join(base_path, today, provider_name)
        create_folder(dir_name)

        return dir_name

    def _rename_latest_downloaded_file(self, new_file_name: str) -> bool:
        """
        Search for the most recently created or modified file in the base folder
        Rename the file and change its location to the full_path
        """
        return rename_latest_file_in_folder(
            self.base_path, self.full_path, new_file_name
        )

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
            sleep(1)
            button.click()
            sleep(1)
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
                case "selector":
                    locator = By.CSS_SELECTOR
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
        write_json(self.products_file, products)

    def _read_products_json(self) -> dict:
        """
        Read the previously saved JSON file
        """
        return read_json(self.products_file)

    def _download_file_with_request(self, url: str, file_name: str) -> None:
        """
        Download a file from a URL using requests
        """
        self.logger.info(f"Downloading file from {url}")
        download_file_with_request(url, self.full_path, file_name)

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
