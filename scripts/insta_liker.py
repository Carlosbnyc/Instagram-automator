from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import os
from dotenv import load_dotenv 

load_dotenv()
USERNAME = os.getenv("INSTAGRAM_USERNAME")
PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
TARGET_ACCOUNTS = os.getenv("TARGET_ACCOUNTS").split(",")  



# === CHROMEDRIVER SETUP ===
CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("user-data-dir=./chrome-session")  # Keeps login session active
options.add_argument("--disable-blink-features=AutomationControlled")  # Helps avoid bot detection
service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)

def random_pause(min_time=2, max_time=5):
    """Adds a random pause to mimic human interaction"""
    time.sleep(random.uniform(min_time, max_time))

def login():
def login():
    """Logs into Instagram and ensures login is successful"""
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(5)  # Let page load

    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(USERNAME)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.NAME, "password"))).send_keys(PASSWORD + Keys.RETURN)

        WebDriverWait(driver, 15).until(EC.url_changes("https://www.instagram.com/accounts/login/"))
        print("✅ Login successful!")

    except Exception as e:
        print(f"❌ Login error: {e}")


def like_latest_posts(profile_url, num_posts=2):
    """Finds and likes the first `num_posts` posts of a profile"""
    driver.get(profile_url)
    random_pause(3, 5)

    try:
        # Find first `num_posts` posts
        posts = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//a[contains(@href, "/p/") or contains(@href, "/reel/")]'))
        )[:num_posts]

        for post in posts:
            try:
                driver.execute_script("arguments[0].scrollIntoView();", post)
                post.click()
                random_pause(3, 5)

                # Like the post if not already liked
                try:
                    like_button = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, '//button[.//span[@aria-label="Like"]]'))
                    )
                    like_button.click()
                    print(f"❤️ Liked post on {profile_url}")
                except:
                    print(f"⚠️ Post already liked on {profile_url}")

                random_pause(2, 4)

                # Close the post modal
                try:
                    close_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, '//button[contains(@aria-label, "Close")]'))
                    )
                    close_button.click()
                except:
                    print("⚠️ Could not close the post modal.")

                random_pause(2, 4)

            except Exception as e:
                print(f"⚠️ Skipping post on {profile_url} due to error: {e}")

    except Exception as e:
        print(f"❌ No posts found or error loading posts on {profile_url}: {e}")

def get_like_count():
    """Extracts the number of likes on an Instagram post"""
    try:
        like_count_xpath = '//a[contains(@href, "/liked_by/")]/span'
        like_button_xpath = '//a[contains(@href, "/liked_by/")]'

        try:
            like_count = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, like_count_xpath))
            ).text
        except:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, like_button_xpath))
            ).click()
            random_pause(3, 5)
            like_count = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//div[@role="dialog"]//div[@role="heading"]'))
            ).text.replace("Likes", "").strip()

        print(f"❤️ Likes: {like_count}")
        return like_count

    except Exception as e:
        print(f"❌ Could not retrieve like count: {e}")
        return None

def scroll_likers_modal():
    """Scrolls through the likers modal to load more users"""
    dialog = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//div[@role="dialog"]')))
    last_height = driver.execute_script("return arguments[0].scrollHeight;", dialog)

    for _ in range(5):  # Scroll 5 times
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", dialog)
        random_pause(2, 4)
        new_height = driver.execute_script("return arguments[0].scrollHeight;", dialog)
        if new_height == last_height:
            break
        last_height = new_height

def like_likers_posts():
    """Finds users who liked the post and likes their first 2 posts"""
    try:
        print("🔍 Finding users who liked this post...")

        # Open likers dialog
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//a[contains(@href, "/liked_by/")]'))
        ).click()

        random_pause(3, 5)
        scroll_likers_modal()

        # Extract likers' profile links (excluding already-followed users)
        likers = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.XPATH, '//div[@role="dialog"]//a[contains(@href, "/")][not(.//div[text()="Following"])]'))
        )
        user_urls = [user.get_attribute("href") for user in likers[:5]]

        for user_url in user_urls:
            like_latest_posts(user_url, num_posts=2)

        # Close the likers modal
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(@aria-label, "Close")]'))
        ).click()
        random_pause(2, 4)

    except Exception as e:
        print(f"🚨 Error finding likers' posts: {e}")

# === RUN SCRIPT ===
login()

while True:
    for account in TARGET_ACCOUNTS:
        print(f"📌 Checking account: {account}")
        like_latest_posts(f"https://www.instagram.com/{account}/", num_posts=2)

        driver.get(f"https://www.instagram.com/{account}/")
        random_pause(3, 5)
        
        try:
            first_post = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//a[contains(@href, "/p/") or contains(@href, "/reel/")]'))
            )
            first_post.click()
            random_pause(3, 5)

            get_like_count()
            like_likers_posts()

        except Exception as e:
            print(f"❌ Error interacting with post: {e}")

    print("⏳ Sleeping before next cycle...")
    time.sleep(3600)