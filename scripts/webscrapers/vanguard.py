from time import sleep

from base_scraper import BaseScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

# Set the URL of the website
ALL_PRODUCTS_PAGE = "https://www.it.vanguard/professional/prodotti?tipo-di-prodotto=etf"


class VanguardScraper(BaseScraper):
    def __init__(self) -> None:
        super().__init__(provider_name="vanguard")

    def handle_initial_banners(self) -> None:
        """
        Handle the initial banners that appear when opening the website
        The banners are:
            - Cookies banner
            - Professional investors banner
        """
        decline_cookies_xpath = '//*[@id="onetrust-reject-all-handler"]'
        self._click_button_by_xpath(xpath=decline_cookies_xpath, btn_name="cookie")

        confirm_professional_xpath = """//*[@id="mat-dialog-0"]/
        europe-core-cookie-consent-dialog/mat-dialog-content/
        europe-core-consent-box/div/div[2]/div[2]/button[1]"""
        self._click_button_by_xpath(
            xpath=confirm_professional_xpath, btn_name="professional investor"
        )

    def get_products_json(self) -> dict:
        """
        Get Vanguard's products JSON
        The JSON' structure can be seen in the file "./output_examples/vanguard.json"
        """
        self.logger.info("Cycling through products table")
        table_xpath = """//*[@id="back-to-top"]/europe-core-root/europe-core-app-main/
                    aem-page/aem-model-provider/aem-responsivegrid/div/aem-responsivegrid/
                    div[4]/europe-core-product-list-tab-group-container/div/div/div/
                    europe-core-product-list-tab-item-container/div/europe-core-overview-table-container/
                    europe-core-product-table/table/"""

        tbody_element_equity = self._get_located_element(f"{table_xpath}/tbody[2]")

        tbody_element_bond = self._get_located_element(f"{table_xpath}/tbody[4]")

        tbody_element_multi_asset = self._get_located_element(
            f"{table_xpath}/tbody[6]"
        )

        def _cycle_trough_tbody(tbody_element: WebElement, asset_class: str) -> dict:
            results = {}
            trows = tbody_element.find_elements(By.TAG_NAME, "tr")

            for row in trows:
                # Product name and page
                th = row.find_element(By.XPATH, ".//th")
                a_element = th.find_element(By.TAG_NAME, "a")
                name = ("Vanguard " + th.text).replace("\n", " ")
                product_page = a_element.get_attribute("href")

                # Currency
                currency = row.find_element(By.XPATH, ".//td[1]").text
                # TER
                ter = row.find_element(By.XPATH, ".//td[2]").text
                # Price
                price = row.find_element(By.XPATH, ".//td[3]").text
                # Date
                date = row.find_element(By.XPATH, ".//td[4]").text
                # ISIN number
                isin = row.find_element(By.XPATH, ".//td[5]").text
                # Ticker
                ticker = row.find_element(
                    By.XPATH, ".//td[6]"
                ).text  # TODO: bloomberg exchange mapping: https://www.inforeachinc.com/bloomberg-exchange-code-mapping
                # Factsheet
                factsheet = row.find_element(By.XPATH, ".//td[7]/span/a").get_attribute(
                    "href"
                )
                # KID
                kid = row.find_element(By.XPATH, ".//td[8]/span/a").get_attribute(
                    "href"
                )

                results[isin] = {
                    "name": name,
                    "ticker": ticker,
                    "asset_class": asset_class,
                    "currency": currency,
                    "ter": ter,
                    "price": price,
                    "date": date,
                    "factsheet": factsheet,
                    "kid": kid,
                    "product_page": product_page,
                }

            return results

        products_dict = {}
        equity = _cycle_trough_tbody(tbody_element_equity, "equity")
        bond = _cycle_trough_tbody(tbody_element_bond, "bond")
        multi_asset = _cycle_trough_tbody(tbody_element_multi_asset, "multi_asset")
        products_dict = {
            **equity,
            **bond,
            **multi_asset,
        }  # unpack dictionaries into one

        self._write_products_json(products_dict)

        return products_dict

    def _download_single_product_holdings(
        self, asset_class: str, isin_number: str, product_page: str
    ) -> None:
        """
        Download the holdings file from the single product page
        """
        self.logger.info(f"Downloading the holdings file from {product_page}")

        self.open_web_page(product_page)
        sleep(1)

        # Download the holdings file, xpath changes based on product type
        button_xpath = """//*[@id="back-to-top"]/europe-core-root/europe-core-product-page/
                        aem-page/aem-model-provider/aem-responsivegrid/div/
                        aem-responsivegrid/div[3]/europe-core-jump-links-list/"""
        match asset_class:
            case "equity":
                button_xpath += """div[17]/europe-core-fund-holdings-container/
                                europe-core-fund-holdings/div/div/div[1]/div[2]/
                                europe-core-download-button/button"""
            case "bond":
                button_xpath += """div[18]/europe-core-fund-holdings-container/
                                europe-core-fund-holdings/div/div/div[1]/div[2]/
                                europe-core-download-button/button"""
            case "multi_asset":
                button_xpath += """div[11]/europe-core-basket-details-container/
                                europe-core-basket-details/div/div/div/div[2]/
                                europe-core-download-button/button"""
            case _:
                self.logger.error(f"Unknown product type: {asset_class}")
                raise ValueError(f"Unknown product type div: {asset_class}")

        download_button = self._get_located_element(button_xpath)

        download_button.click()
        sleep(3)  # Wait for the download to finish and not overload the server

        # Rename the file as the ISIN number
        self._rename_latest_downloaded_file(new_file_name=f"{isin_number}")

    def download_product_files(self, products_dict: dict) -> None:
        # Cycle trough each product by ISIN
        for isin in products_dict.keys():
            product_page = products_dict[isin]["product_page"]
            self._download_single_product_holdings(
                products_dict[isin]["asset_class"], isin, product_page
            )


def main():
    scraper = VanguardScraper()
    scraper.open_web_page(ALL_PRODUCTS_PAGE)
    scraper.handle_initial_banners()
    products_dict = scraper.get_products_json()
    scraper.download_product_files(products_dict)
    scraper.quit()


if __name__ == "__main__":
    main()
