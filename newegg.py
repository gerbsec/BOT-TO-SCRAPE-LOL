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
from selenium.webdriver.common import action_chains
import os
from pprint import pprint

# Twilio credentials

twilio_sid = ""
twilio_authtoken = ""
client = Client(twilio_sid, twilio_authtoken)

class NeweggSpider(scrapy.Spider):
    name = "newegg"

    firefox_profile_path = os.environ["FIREFOX_PROFILE"]
    
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) " \
                 "Chrome/43.0.2357.130 Safari/537.36"

    # product_url = "https://www.newegg.com/p/pl?d=3080&N=100007709%204841%2050001314%204021%2050001315%2050001312%2050001402&isdeptsrh=1"
    product_url = 'https://www.newegg.com/adata-model-auv350-64g-rbk-64gb/p/N82E16820215341?Item=N82E16820215341&quicklink=true'

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
        add_to_cart_xpath = "//*[@class='btn btn-primary btn-wide']" # Use btn-wide if you are using a link for a specific item, and btn-mini for a list
        # Wait until we can click on the add to cart button
        self.wait.until(
            EC.visibility_of_element_located((By.XPATH, add_to_cart_xpath)))
        time.sleep(.5)
        self.driver.find_element_by_xpath(
            add_to_cart_xpath).click()

    def get_products(self):
        self.products = self.driver.find_element_by_xpath(
            "//*[@class='btn btn-primary btn-mini']").text.strip()

    def product_available(self):
        return len(self.products)
    
    def ensure_success(self):
        print("\nEnsuring that product is in fact, in the cart.\n")
        time.sleep(1)
        available = self.driver.find_element_by_xpath(
            "//*[@class='btn btn-primary btn-wide']").is_enabled()
        if available:
            print("It is!")
            client.messages \
                    .create(
                        body="Bot just added item to cart, check it out!",
                        from_='Twilio Number',
                        to='Your Number'
                    )
        else:
            print("f")
            yield Request(self.product_url, callback=self.parse, dont_filter=True)

    def parse(self, response, *args, **kwargs):
        self.driver.get(self.product_url)
        # Finding Product Availability.
        try:
            self.get_products()
            if self.product_available():
                print("\nProduct is Available.\n")
                self.add_to_cart()
        except (AttributeError, NoSuchElementException, WebDriverException, TimeoutException):
            print("\nProduct Sold Out: Retrying in 3 Seconds.\n")
            time.sleep(3)
            yield Request(self.product_url, callback=self.parse, dont_filter=True)
        # Checking to make sure product is in cart
        if self.product_available():
            # Going to Check Out Page. (Page 2)
            print("\nHopefully, in cart now!\n")
            self.driver.get(
                "https://secure.newegg.com/Shopping/ShoppingCart.aspx?Submit=view")
        time.sleep(.5)
        try:
            self.ensure_success()
        except (AttributeError, NoSuchElementException, WebDriverException, TimeoutException):
            print("f")
            yield Request(self.product_url, callback=self.parse, dont_filter=True)