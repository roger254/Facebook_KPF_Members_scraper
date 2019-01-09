import json
import os
import re

import pyrebase as pyrebase
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

# environment variables
FACEBOOK_EMAIL = os.getenv('FACEBOOK_EMAIL', )
FACEBOOK_PASS = os.getenv('FACEBOOK_PASSWORD', )
CHROME_PATH = os.getenv('CHROME_PATH')

url_main = 'https://www.facebook.com/'
url_page = 'https://www.facebook.com/groups/kenyapolitforum/'
members_id_expression = re.compile('recently_joined_[0-9]+')
return_data = []


def load_pyre():
    config = {
        'apiKey': os.getenv('apiKey'),
        'authDomain': os.getenv('authDomain'),
        'databaseURL': os.getenv('databaseURL'),
        'storageBucket': os.getenv('storageBucket')
    }
    pyre = pyrebase.initialize_app(config)
    db = pyre.database()
    return db


def get_driver():
    chrome_options = webdriver.ChromeOptions()
    # remove notifications
    chrome_options.add_experimental_option(
        "prefs",
        {
            "profile.default_content_setting_values.notifications": 2
        }
    )
    main_driver = webdriver.Chrome(executable_path=CHROME_PATH, options=chrome_options)
    main_driver.maximize_window()
    return main_driver


driver = get_driver()


# login to facebook
def login_to_facebook():
    login_driver = driver
    login_driver.get(url_main)
    login_driver.find_element_by_id('email').send_keys(FACEBOOK_EMAIL)
    login_driver.find_element_by_id('pass').send_keys(FACEBOOK_PASS)
    login_driver.find_element_by_id('loginbutton').click()


def extract_data(soup):
    members = soup.find_all('div', id=members_id_expression)
    for a in members:
        user_data = {}
        user_data['name'] = a.find('div', class_='_60ri').find('a').text
        info = a.find_all('div', class_='_60rj')
        user_data['Joining Info'] = info[0].text
        user_data['Personal Info'] = info[1].text
        return_data.append(user_data)


def get_details():
    login_to_facebook()
    driver.get(url_page)
    WebDriverWait(driver, 30).until(ec.presence_of_all_elements_located((By.ID, 'mainContainer')))
    # click members button
    members_button = driver.find_element_by_xpath('//*[@id="u_0_u"]/div[3]/a/span[1]')
    driver.execute_script('arguments[0].click();', members_button)
    WebDriverWait(driver, 30).until(ec.presence_of_all_elements_located((By.ID, 'groupsMemberSection_recently_joined')))

    # scroll to bottom part
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        WebDriverWait(driver, 30).until(
            ec.presence_of_all_elements_located((By.CLASS_NAME, 'expandedList')))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        members = soup.find_all('div', id=members_id_expression)
        if len(members) > 100:
            extract_data(soup)
            break


def save_data():
    db = load_pyre()
    for data in return_data:
        db.child('/Group_Members').child(data['name']).set(data)


try:
    get_details()
    save_data()
except Exception as e:
    print(e)
finally:
    driver.close()
