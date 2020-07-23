import re
import sys
import time
import socket
import http

from selenium import webdriver
from selenium.webdriver import DesiredCapabilities

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

from selenium.common.exceptions import NoAlertPresentException


URL = 'http://vk.com'
TIMEOUT = 100
HEADLESS = 0

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'


def wait(driver, *args, **kwargs):
    try:
        return WebDriverWait(driver, TIMEOUT).until(*args, **kwargs)
    except Exception as e:
        return


def setup_driver(headless=True):
    try:
        chrome_options = Options()
        chrome_options.add_argument('--mute-audio')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument(f'user-agent={USER_AGENT}')

        headless and chrome_options.add_argument('--headless')

        prefs = {'profile.managed_default_content_settings.images': 2}
        chrome_options.add_experimental_option('prefs', prefs)

        dc = DesiredCapabilities.CHROME
        dc['loggingPrefs'] = {'browser': 'ALL'}

        driver = webdriver.Chrome(options=chrome_options,
                                  desired_capabilities=dc)

        max_wait = TIMEOUT
        driver.set_window_size(1000, 1000)
        driver.set_page_load_timeout(max_wait)
        driver.set_script_timeout(max_wait)
    except Exception as e:
        print(e)

    return driver


def scrape(driver):
    wait(driver, EC.presence_of_element_located(
        #(By.CSS_SELECTOR, '.audio_pl .audio_row__performer_title')))
        (By.CSS_SELECTOR, '.audio_section .audio_row__performer_title')))

    for link in driver.find_elements_by_class_name('audio_row__performer_title'):
        print(' ||| '.join(link.text.split('\n')))

    driver.execute_script('''
        document.querySelectorAll('.audio_row')
            .forEach(function(element) {
                element.remove()
        });

        window.scroll(0, 10);
        window.scroll(0, -10);
    ''')

    return 1


if __name__ == '__main__':
    try:
        driver = setup_driver(headless=HEADLESS)
        driver.get(URL)

        while scrape(driver): pass

    except (socket.error,
            KeyboardInterrupt,
            http.client.RemoteDisconnected) as e:
        print(e, type='error')
