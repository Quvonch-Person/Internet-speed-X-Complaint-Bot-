import os
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

load_dotenv()

PROMISED_DOWN = 100  # Mbps
PROMISED_UP = 20    # Mbps
TWITTER_EMAIL = os.getenv("TWITTER_EMAIL")
TWITTER_PASSWORD = os.getenv("TWITTER_PASSWORD")
TWITTER_USERNAME = os.getenv("TWITTER_USERNAME")
ISP_HANDLE = "@YourISP"


class InternetSpeedTwitterBot:
    def __init__(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option("detach", True)
        chrome_options.add_argument("--start-maximized")
        # Suppress notification prompts
        chrome_options.add_experimental_option(
            "prefs", {"profile.default_content_setting_values.notifications": 2}
        )

        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 15)
        self.down = 0.0
        self.up = 0.0

    def get_internet_speed(self):
        print("Opening Speedtest.net...")
        self.driver.get("https://www.speedtest.net/")

        # Dismiss GDPR / Cookie modal if present
        try:
            cookie_accept = self.wait.until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            cookie_accept.click()
            print("Accepted cookies.")
        except TimeoutException:
            pass

        # Click the "Go" button to start the test
        time.sleep(1)
        go_button = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".start-button a"))
        )
        go_button.click()
        print("Speed test in progress... (this takes ~45 seconds)")

        # Wait for the results to populate and finish
        # The test completes when the desktop result link/banner appears or wait times out
        result_wait = WebDriverWait(self.driver, 60)
        result_wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".result-item-id"))
        )

        down_elem = self.driver.find_element(By.CSS_SELECTOR, ".download-speed")
        up_elem = self.driver.find_element(By.CSS_SELECTOR, ".upload-speed")

        self.down = float(down_elem.text.strip())
        self.up = float(up_elem.text.strip())
        print(f"Recorded Speeds -> Download: {self.down} Mbps | Upload: {self.up} Mbps")

    def tweet_at_provider(self):
        print("Navigating to X/Twitter login...")
        self.driver.get("https://x.com/i/flow/login")

        # Step 1: Input Email/Username
        email_input = self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@autocomplete='username']"))
        )
        email_input.send_keys(TWITTER_EMAIL)
        email_input.send_keys(Keys.ENTER)

        # Step 2: Handle unusual login verification prompt (if triggered)
        time.sleep(2)
        try:
            extra_auth_input = self.driver.find_element(
                By.XPATH, "//input[@data-testid='ocfEnterTextTextInput']"
            )
            print("Twitter requested phone/username verification...")
            extra_auth_input.send_keys(TWITTER_USERNAME)
            extra_auth_input.send_keys(Keys.ENTER)
        except NoSuchElementException:
            pass

        # Step 3: Input Password
        password_input = self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@name='password']"))
        )
        password_input.send_keys(TWITTER_PASSWORD)
        password_input.send_keys(Keys.ENTER)

        # Step 4: Locate Tweet Box & Post
        tweet_box = self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@role='textbox' and @data-testid='tweetTextarea_0']")
            )
        )

        tweet_message = (
            f"Hey {ISP_HANDLE}, why is my internet speed {self.down}down/{self.up}up "
            f"when I pay for {PROMISED_DOWN}down/{PROMISED_UP}up?"
        )

        tweet_box.send_keys(tweet_message)
        time.sleep(1)

        post_button = self.driver.find_element(
            By.XPATH, "//button[@data-testid='tweetButtonInline']"
        )
        post_button.click()
        print("Complaint tweet successfully posted.")


# ==========================================
# EXECUTION
# ==========================================
bot = InternetSpeedTwitterBot()
bot.get_internet_speed()

if bot.down < PROMISED_DOWN or bot.up < PROMISED_UP:
    print(f"Speed below promised limits. Triggering complaint bot...")
    bot.tweet_at_provider()
else:
    print("Internet speed meets specifications. No action required.")