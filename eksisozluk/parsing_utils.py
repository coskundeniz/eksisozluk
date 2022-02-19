import os
import random
from typing import Optional, Union

import bs4
from bs4 import BeautifulSoup
import requests
import selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
    WebDriverException,
)
from selenium.webdriver import FirefoxOptions, ChromeOptions
from webdriver_setup import get_webdriver_for

from eksisozluk.constants import PAGE_URL, USER_AGENT_LIST
from eksisozluk.exceptions import EksiReaderPageRequestError


def parse_page(url: str, timeout: float = 3.0) -> BeautifulSoup:
    """Open and parse page content

    :type url: str
    :param url: url of the page to be parsed
    :rtype: BeautifulSoup
    :returns: BeautifulSoup object
    """

    # pick a random user agent
    user_agent = random.choice(USER_AGENT_LIST)
    headers = {"User-Agent": user_agent}

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
    except (
        requests.exceptions.HTTPError,
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.RequestException,
    ) as exp:
        raise EksiReaderPageRequestError(f"Request failed for {url}!") from exp

    parsed_page = BeautifulSoup(response.content, "html.parser")

    return parsed_page


def find_element_with_id(
    element_id: str, content: bs4.element.Tag
) -> Optional[bs4.element.Tag]:
    """Find element with given id

    :type element_id: str
    :param element_id: id of element
    :type content: bs4.element.Tag
    :param content: Content to be searched
    :rtype: bs4.element.Tag
    :returns: Element found or None
    """

    try:
        element = content.find(id=element_id)
    except:
        return None

    return element


def find_elements_with_class(
    tag: str, element_class: str, content: bs4.element.Tag
) -> bs4.element.ResultSet:
    """Find elements for tag that has given class

    :type tag: str
    :param tag: class of element
    :type element_class: str
    :param element_class: class of element
    :type content: bs4.element.Tag
    :param content: Content to be searched
    :rtype: bs4.element.ResultSet
    :returns: List of elements found or empty list
    """

    return content.find_all(tag, {"class": element_class})


def find_elements_with_tag(tag: str, content: bs4.element.Tag) -> bs4.element.ResultSet:
    """Find elements with given tag

    :type tag: str
    :param tag: class of element
    :type content: bs4.element.Tag
    :param content: Content to be searched
    :rtype: bs4.element.ResultSet
    :returns: List of elements found or empty list
    """

    return content.find_all(tag)


def select_first_element(
    element_class: str, content: bs4.element.Tag
) -> Union[bs4.element.Tag, list]:
    """Select first element with given class

    :type element_class: str
    :param element_class: class of element
    :type content: bs4.element.Tag
    :param content: Content to be searched
    :rtype: bs4.element.Tag
    :returns: First element found or empty list
    """

    try:
        element = content.select("." + element_class)[0]
    except IndexError:
        element = []

    return element


def select_all_elements(
    element_class: str, content: bs4.element.Tag
) -> bs4.element.ResultSet:
    """Select all elements with given class

    :type element_class: str
    :param element_class: class of elements
    :type content: bs4.element.Tag
    :param content: Content to be searched
    :rtype: bs4.element.ResultSet
    :returns: List of elements found or empty list
    """

    return content.select("." + element_class)


def get_elements_with_css_selector(
    selector: str, content: bs4.element.Tag
) -> bs4.element.ResultSet:
    """Select all elements with given css selector

    :type selector: str
    :param selector: css selector
    :type content: bs4.element.Tag
    :param content: Content to be searched
    :rtype: bs4.element.ResultSet
    :returns: List of elements found or empty list
    """

    return content.select(selector)


def get_element_attribute(attribute: str, element: bs4.element.Tag) -> Optional[str]:
    """Get attribute value of the given element

    :type attribute: str
    :param attribute: attribute name
    :type element: bs4.element.Tag
    :param element: BeautifulSoup element
    :rtype: str
    :returns: Attribute value or None
    """

    try:
        value = element[attribute]
    except:
        value = None

    return value


def get_element_text_content(element: bs4.element.Tag) -> str:
    """Get text content of the given element

    :type element: bs4.element.Tag
    :param element: BeautifulSoup element
    :rtype: str
    :returns: Text content or empty string
    """

    try:
        text = element.text.strip()
    except:
        text = ""

    return text


def handle_br_tag(element: bs4.element.Tag) -> str:
    """Replace "<br/>" with "\n"

    :type entry_element: bs4.element.Tag
    :param entry_element: Tag element
    :rtype: str
    :returns: "\n" if element is br, empty string otherwise
    """

    return "\n" if element.name == "br" else ""


def handle_a_tag(element: bs4.element.Tag) -> str:
    """Construct string to represent link text with url

    :type entry_element: bs4.element.Tag
    :param entry_element: Tag element
    :rtype: str
    :returns: Link text representation
    """

    link_text = ""
    if element.name == "a":

        if "spoiler" in element.text or "http" in element.text:
            link_text += f" {element.text} "
        elif "http" not in element["href"]:  # internal link
            link_text += f" {element.text} ({PAGE_URL}{element['href']}) "
        else:
            link_text += f" {element.text}({element['href']}) "

    return link_text


def create_driver() -> selenium.webdriver:
    """Create browser driver

    Firefox is tried first. If it fails, Chrome is tried.

    :rtype: selenium.webdriver
    :returns: Selenium webdriver instance
    """

    os.environ["WDM_LOG_LEVEL"] = "0"

    try:
        firefox_options = FirefoxOptions()
        firefox_options.add_argument("--headless")
        driver = get_webdriver_for("firefox", options=firefox_options)

    except WebDriverException:
        chrome_options = ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-dev-shm-usage")
        driver = get_webdriver_for("chrome", options=chrome_options)

    return driver


def wait_for_element_to_load(
    driver: selenium.webdriver, selector: str
) -> BeautifulSoup:
    """Wait for the element to load with the given selector

    Raises EksiReaderPageRequestError if timeout occurs while
    waiting for the element.

    :type driver: selenium.webdriver
    :param driver: Selenium webdriver instance
    :type selector: str
    :param selector: Css selector
    :rtype: BeautifulSoup
    :returns: Element as BeautifulSoup object
    """

    try:
        wait = WebDriverWait(driver, timeout=5)
        element_visible = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
        )

        if element_visible:
            element = driver.find_elements(By.CSS_SELECTOR, selector)[-1]
            soup = BeautifulSoup(element.get_attribute("outerHTML"), "html.parser")
            return soup

    except TimeoutException as exp:
        raise EksiReaderPageRequestError(
            "Timed out waiting for element to load!"
        ) from exp


def click_load_more(driver: selenium.webdriver) -> None:
    """Click load more button

    Raises EksiReaderPageRequestError if timeout occurs while
    waiting for the load more button element to be clickable.

    :type driver: selenium.webdriver
    :param driver: Selenium webdriver instance
    """

    try:
        wait = WebDriverWait(driver, timeout=5)
        element_clickable = wait.until(
            EC.invisibility_of_element_located((By.ID, "onetrust-policy"))
        )

        if element_clickable:
            element = driver.find_element(By.CLASS_NAME, "load-more-entries")
            element.click()

    except TimeoutException as exp:
        raise EksiReaderPageRequestError(
            "Timed out waiting for load more button element to be clickable!"
        ) from exp


def close_cookie_dialog(driver: selenium.webdriver) -> None:
    """Close cookie dialog if exists

    :type driver: selenium.webdriver
    :param driver: Selenium webdriver instance
    """

    try:
        cookie_dialog = driver.find_element(
            By.CSS_SELECTOR, ".onetrust-close-btn-handler"
        )
        cookie_dialog.click()
    except (NoSuchElementException, ElementNotInteractableException):
        pass
