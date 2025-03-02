from time import sleep
from urllib.parse import parse_qs, urlparse

from base_scraper import BaseScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

# Set the URL of the website
ALL_PRODUCTS_PAGE = (
    "https://www.ishares.com/it/investitore-privato/it/prodotti/etf-investments"
)


class ISharesScraper(BaseScraper):
    def __init__(self) -> None:
        super().__init__(provider_name="ishares")

    def handle_initial_banners(self) -> None:
        """
        Handle the initial banners that appear when opening the website
        The banners are:
            - Cookies banner
            - Private investors banner
        """
        decline_cookies_xpath = '//*[@id="onetrust-reject-all-handler"]'
        self._click_button_by_xpath(xpath=decline_cookies_xpath, btn_name="cookie")

        confirm_private_xpath = """//*[@id="direct-url-screen-{lang}"]/div/div[2]/div"""
        self._click_button_by_xpath(
            xpath=confirm_private_xpath, btn_name="professional investor"
        )

    def view_all_products(self) -> None:
        """
        Click the button to view all products
        """
        view_all_xpath = (
            """//*[@id="screener-funds"]/div/screener-show-all-button/button"""
        )
        self._click_button_by_xpath(view_all_xpath, btn_name="View all")

    def _get_intermediate_products_json(self) -> dict:
        """
        Get iShares's products JSON
        The JSON' won't contain all the information required, a further step is necessary to find all required fields
        """
        self.logger.info("Cycling through products table")
        tbody_element = self._get_located_element(
            '//*[@id="screener-funds"]/screener-table/table/tbody'
        )

        def _cycle_trough_tbody(tbody_element: WebElement) -> dict:
            results = {}
            trows = tbody_element.find_elements(By.TAG_NAME, "tr")

            i = 0
            for row in trows:
                # Check that fund type is ETF
                if row.find_element(By.XPATH, ".//td[1]").text != "ETF":
                    continue

                # Product name and page
                th = row.find_element(By.XPATH, ".//th")
                a_element = th.find_element(By.TAG_NAME, "a")
                name = th.text
                product_page = a_element.get_attribute("href")

                # Currency
                currency = row.find_element(By.XPATH, ".//td[2]").text
                # Currency hedging
                hedged = row.find_element(By.XPATH, ".//td[3]").text
                # ACC - DISTR
                acc_distr = row.find_element(By.XPATH, ".//td[4]").text
                # TER
                ter = row.find_element(By.XPATH, ".//td[5]").text
                # Date
                date = row.find_element(By.XPATH, ".//td[7]").text

                results[f"dummy_key_{i}"] = {  # ISIN not directly available
                    "name": name,
                    "currency": currency,
                    "hedged": hedged,
                    "acc_distr": acc_distr,
                    "ter": ter,
                    "date": date,
                    "product_page": product_page,
                }
                i += 1

            return results

        products_dict = {}
        products_dict = _cycle_trough_tbody(tbody_element)

        return products_dict

    def _scrape_single_product_infos(self, product_page: str) -> dict:
        """
        Scrape the product's page to get: ISIN, Ticker, Factsheet, KID, Price
        Also, save the link to the holdings file
        """
        self.open_web_page(product_page)
        sleep(1)

        # ISIN
        isin = self._get_located_element(
            """//div[contains(@class, 'product-data-item') and contains(@class, 'col-isin')]//div[@class='data']"""
        ).text
        # Price
        price = self._get_located_element(
            '//*[@id="fundheaderTabs"]/div/div/div/ul/li[1]/span[2]'
        ).text
        # Ticker
        ticker = self._get_located_element(
            """//div[contains(@class, 'product-data-item') and contains(@class, 'col-bbeqtick')]//div[@class='data']"""
        ).text
        # Factsheet
        factsheet = self._get_located_element(
            '//*[@id="fundHeaderDocLinks"]/li[2]/a'
        ).get_attribute("href")
        # KID
        kid = self._get_located_element(
            '//*[@id="fundHeaderDocLinks"]/li[1]/a'
        ).get_attribute("href")
        # Holdings file
        holdings_file = self._get_located_element(
            '//*[@id="holdings"]/div[2]/a'
        ).get_attribute("href")

        return {
            "isin": isin,
            "ticker": ticker,
            "price": price,
            "factsheet": factsheet,
            "kid": kid,
            "holdings_file": holdings_file,
        }

    def _get_final_products_json(self, intermediate_json: dict) -> dict:
        """
        Enriches the intermediate JSON file with other fields that were not
        possible to gather before this step
        """
        final_json = {}
        for dummy_key in intermediate_json.keys():
            additional_infos = self._scrape_single_product_infos(
                intermediate_json[dummy_key]["product_page"]
            )
            final_json[additional_infos["isin"]] = {
                "name": intermediate_json[dummy_key]["name"].split("\n")[0],
                "fund_type": None,  # TODO: find a way to distinguish between equity bond or multi
                "currency": intermediate_json[dummy_key]["currency"],
                "ter": intermediate_json[dummy_key]["ter"],
                "price": additional_infos["price"],
                "date": intermediate_json[dummy_key]["date"],
                "factsheet": additional_infos["factsheet"],
                "kid": additional_infos["kid"],
                "product_page": intermediate_json[dummy_key]["product_page"],
                "holdings_file": additional_infos["holdings_file"],
            }

        return final_json

    def get_products_json(self) -> dict:
        """
        Get iShares's products JSON
        The JSON' structure can be seen in the file "./output_examples/ishares.json"
        """
        intermediate_json = self._get_intermediate_products_json()
        final_json = self._get_final_products_json(intermediate_json)
        self._write_products_json(final_json)

        return final_json

    def download_product_files(self, products_dict: dict) -> None:
        """
        Download the product files from the website
        """
        for isin, product in products_dict.items():
            url = product["holdings_file"]
            parsed_url = urlparse(url)
            file_extension = parse_qs(parsed_url.query).get("fileType", ["csv"])[0]

            self._download_file_with_request(
                url=product["holdings_file"], file_name=f"{isin}.{file_extension}"
            )
            sleep(0.5)


def main():
    scraper = ISharesScraper()
    scraper.open_web_page(ALL_PRODUCTS_PAGE)
    scraper.handle_initial_banners()
    scraper.view_all_products()
    products_dict = scraper.get_products_json()
    # products_dict = scraper._read_products_json()  # test
    scraper.download_product_files(products_dict)
    scraper.quit()


if __name__ == "__main__":
    main()
