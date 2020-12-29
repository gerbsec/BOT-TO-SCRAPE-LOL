import scrapy
import time
from scrapy.http import Request
from webdriver_manager.firefox import GeckoDriverManager
from selenium import webdriver
from twilio.rest import Client
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options

# Twilio credentials

# client = Client(twilio_email, twilio_password)


class NeweggSpider(scrapy.Spider):
    name = "newegg"

    newegg_password = ""
    twilio_email = ""
    twilio_password = ""

    firefox_profile_path = "/home/gerber/.mozilla/firefox/inr4vjj4.default-release"

    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) " \
                 "Chrome/43.0.2357.130 Safari/537.36 "

    # product_url = "https://www.newegg.com/p/pl?d=3080&N=100007709%204841%2050001314%204021%2050001315%2050001312%2050001402&isdeptsrh=1"
    product_url = 'https://www.newegg.com/adata-model-auv350-32g-rbk-32gb/p/N82E16820215361?Description=usb&cm_re=usb-_-20-215-361-_-Product'

    def __init__(self, *args, **kwargs):
        options = Options()
        options.headless = False

        self.profile = webdriver.FirefoxProfile(self.firefox_profile_path)
        self.driver = webdriver.Firefox(
            self.profile, options=options, executable_path=GeckoDriverManager().install())
        self.wait = WebDriverWait(self.driver, 5)
        self.products = []
        # Link for product, this is 3080 with some presets
        self.start_urls = [self.product_url]

    def add_to_cart(self):
        print("\nFound 1 item to add to cart.\n")
        add_to_cart_xpath = "//*[@class='btn btn-primary btn-wide']"

        # Wait until we can click on the add to cart button
        self.wait.until(
            EC.visibility_of_element_located((By.XPATH, add_to_cart_xpath)))
        time.sleep(.5)
        self.driver.find_element_by_xpath(
            add_to_cart_xpath).click()

    def move_to_checkout(self):
        print("\nClicking Secure Checkout. (Page 2)\n")
        available = self.driver.find_element_by_xpath(
            "//*[@class='btn btn-primary btn-wide']").is_enabled()
        if available:
            time.sleep(1)
            self.driver.find_element_by_xpath(
                "//*[@class='btn btn-primary btn-wide']").click()

    def handle_checkout_steps(self):
        print("\nHandling checkout steps\n")
        xpath = "/html/body/div[7]/div/section/div/div/form/div[2]/div[1]/div/div[2]/div/div[3]/button"
        available = self.driver.find_element_by_xpath(xpath).is_enabled()
        if available:
            time.sleep(1)
            self.driver.find_element_by_xpath(xpath).click()

    def get_products(self):
        self.products = self.driver.find_element_by_xpath(
            "//*[@class='btn btn-primary btn-mini']").text.strip()

    def product_available(self):
        return len(self.products)

    def login_with_password(self):
        # Login Password. (Page 3)
        try:
            print("\nAttempting Password. (Page 3)\n")
            self.wait.until(EC.visibility_of_element_located(
                (By.ID, "labeled-input-password")))
            password = self.driver.find_element_by_id(
                "labeled-input-password")
            password.send_keys(self.newegg_password)
            password.send_keys(Keys.ENTER)
        except (AttributeError, NoSuchElementException, WebDriverException, TimeoutException) as error:
            if error:
                print("\nDid Not Use Password. (Page 3)\n")

    def parse(self, response, *args, **kwargs):
        self.driver.get(self.product_url)
        # Finding Product Availability.
        try:
            self.get_products()

            if self.product_available():
                print("\nProduct is Available.\n")
                self.add_to_cart()
        except (AttributeError, NoSuchElementException, WebDriverException, TimeoutException) as error:
            print("\nProduct Sold Out: Retrying in 3 Seconds.\n")
            time.sleep(3)
            yield Request(self.product_url, callback=self.parse, dont_filter=True)

        if self.product_available():
            # Going to Check Out Page. (Page 2)

            print("\nGoing to Checkout Cart. (Page 2)\n")
            self.driver.get(
                "https://secure.newegg.com/Shopping/ShoppingCart.aspx?Submit=view")
            try:
                self.move_to_checkout()
            except (AttributeError, NoSuchElementException, WebDriverException, TimeoutException) as error:
                print("\nSecuring Checkout button is not Clickable.\n")
                print(error)
                time.sleep(3)
                yield Request(self.product_url, callback=self.parse, dont_filter=True)

            
            try:
                self.handle_checkout_steps()
            except (AttributeError, NoSuchElementException, WebDriverException, TimeoutException) as error:
                print("\nUnable to handle checkout steps\n")
                print(error)
                time.sleep(3)
                yield Request(self.product_url, callback=self.parse, dont_filter=True)

            # Submit CVV Code(Must type CVV number. (Page 4)
            try:
                print("\nTrying Credit Card CVV Number. (Page 4)\n")
                self.wait.until(EC.visibility_of_element_located(
                    (By.XPATH, "//input[@class='form-text mask-cvv-4'][@type='text']")))
                security_code = self.driver.find_element_by_xpath(
                    "//input[@class='form-text mask-cvv-4'][@type='text']")
                time.sleep(1)
                security_code.send_keys(
                    Keys.BACK_SPACE + Keys.BACK_SPACE + Keys.BACK_SPACE + "123")  # You can enter your CVV number here.!!!!!!!!!
            except (AttributeError, NoSuchElementException, WebDriverException, TimeoutException) as error:
                if error:
                    print("\nCould Not Type CVV. (Page 4)\n")

            # ARE YOU READY TO BUY? (Page 4) COMMENT BELOW OUT IF YOU DONT WANT IT TO BUY STUFF

            # try:
            #     print("\nBuying Product. (Page 4)\n")
            #     time.sleep(.5)
            #     final_step = self.driver.find_element_by_id(
            #         "btnCreditCard").is_enabled()
            #     if final_step:
            #         print("\nFinalizing Bot!...\n")
            #         # self.driver.find_element_by_id("btnCreditCard").click()
            #         time.sleep(5)
            #         print("\nBot has Completed Checkout.\n")
            #         # Want to Receive Text Messages?
            #         # client.messages.create(to="+1your number", from_="+1twilio number",
            #         #                        body="Bot made a Purchase. newegg !")
            # except (AttributeError, NoSuchElementException, WebDriverException, TimeoutException) as error:
            #     if error:
            #         print("\nRestarting: Checkout Did Not Go Through. (Page 4)\n")
            #         time.sleep(3)
            #         yield Request(self.product_url, callback=self.parse, dont_filter=True)
