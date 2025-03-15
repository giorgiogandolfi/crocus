from abc import ABC, abstractmethod

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait


class BaseFirefoxDriver(ABC):
    """
    This class provides a base implementation for initializing and configuring
    Selenium WebDriver instances

    Methods:
        __init__(): Initializes the BaseWebDriver instance with dummy attributes
        _get_webdriver_options(): Configures and returns Options for the WebDriver
        get_driver(): Returns the current WebDriver instance
        get_wait(): Returns the current WebDriverWait instance
    """

    @abstractmethod
    def __init__(self):
        self._driver = None
        self._wait = None

    def _get_webdriver_options(
        self, download_path: str, headless: bool = False
    ) -> Options:
        options = Options()

        # Use a custom download directory
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.dir", download_path)
        options.set_preference("browser.download.useDownloadDir", True)

        # Disable the download manager window popup
        options.set_preference("browser.download.manager.showWhenStarting", False)

        # Automatically save files for specified MIME types without prompting
        mime_types = (
            "application/csv,application/vnd.ms-excel,"
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", mime_types)

        # Disable the built-in PDF viewer so that PDFs are downloaded
        options.set_preference("pdfjs.disabled", True)

        # Additional enhancements:
        options.set_preference("browser.download.manager.alertOnEXEOpen", False)
        options.set_preference("browser.helperApps.alwaysAsk.force", False)
        options.set_preference("browser.download.manager.focusWhenStarting", False)

        # Disable GPU acceleration
        options.add_argument("--disable-gpu")

        # Disable the sandbox
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-setuid-sandbox")

        # Headless option
        if headless:
            options.add_argument("--headless")

        return options

    def get_driver(self) -> webdriver.Firefox | webdriver.Remote:
        return self._driver

    def get_wait(self) -> WebDriverWait:
        return self._wait


class LocalFirefoxDriver(BaseFirefoxDriver):
    """
    Represents a local Firefox WebDriver for web scraping
    This class is mainly used for local tests

    Attributes:
        _driver (webdriver.Firefox): An instance of Firefox WebDriver
        _wait (WebDriverWait): An instance of WebDriverWait for explicit waits

    Methods:
        __init__(download_path: str): Initializes the LocalFirefoxWebDriver with the specified download path
    """

    def __init__(self, download_path: str):
        options = self._get_webdriver_options(
            download_path=download_path, headless=False
        )
        self._driver = webdriver.Firefox(options=options)
        self._wait = WebDriverWait(self._driver, 20)


class RemoteFirefoxWebDriver(BaseFirefoxDriver):
    """
    A web driver that connects to a remote Selenium server to control a Firefox browser

    Args:
        download_path (str): The path where files downloaded by the browser will be saved
        server (str, optional): The URL of the remote Selenium server. Defaults to "http://localhost:4444"
        headless (bool, optional): Whether to run the browser in headless mode. Defaults to False

    Attributes:
        _driver (webdriver.Remote): The remote web driver instance
        _wait (WebDriverWait): The wait utility for the web driver
    """

    def __init__(
        self, download_path: str, server: str = "http://selenium:4444", headless=False
    ):
        options = self._get_webdriver_options(
            download_path=download_path, headless=headless
        )
        self._driver = webdriver.Remote(command_executor=server, options=options)
        self._wait = WebDriverWait(self._driver, 20)
