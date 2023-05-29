import os
import time
from getpass import getpass
from playwright.sync_api import sync_playwright

import logging

logger = logging.getLogger("main")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
logger.addHandler(handler)


KEY1_VAR_NAME = "Unicorn_Secret1"
KEY2_VAR_NAME = "Unicorn_Secret2"


def set_secret():
    print("Please supply access codes for the script to work.")
    os.environ[KEY1_VAR_NAME] = getpass("Access Code 1: ")
    os.environ[KEY2_VAR_NAME] = getpass("Access Code 2: ")


def get_secret(wrong=False):
    if (
        not os.environ.get(KEY1_VAR_NAME) and not os.environ.get(KEY2_VAR_NAME)
    ) or wrong:
        if wrong:
            logger.info("Wrong access codes.")
        set_secret()

    return {
        "secret1": os.environ.get(KEY1_VAR_NAME),
        "secret2": os.environ.get(KEY2_VAR_NAME),
    }


def login(context, secret):
    inputs = context.locator("input[type=password]")
    inputs.nth(0).fill(secret["secret1"])
    inputs.nth(1).fill(secret["secret2"])
    context.get_by_role("button", name="Log in").click()
    time.sleep(2)


def print_pdf(page_object, name, count=None):
    page_object.emulate_media(media="print")
    FOLDER = "PDFs"
    opts = {"format": "A4", "print_background": True, "scale": 0.87}
    if not count:
        page_object.pdf(path=f"{FOLDER}/{name}.pdf", **opts)
    else:
        page_object.pdf(path=f"{FOLDER}/{name}_{count}.pdf", **opts)
    page_object.emulate_media(media="screen")


def main():
    secret = get_secret()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(input("uuBook URL: "))
        with page.expect_popup() as popup_info:
            page.click(".plus4u5-app-button:visible")
        popup = popup_info.value
        popup.wait_for_load_state()

        login(popup, secret)

        # TODO: Implement failed login re-attempt
        """
        while popup.locator("div[class='uu5-bricks-alert-content']").is_visible():
            login(popup, get_secret(wrong=True))
        """

        menu = page.locator(".plus4u5-app-menu:visible")
        items = menu.locator(
            ".plus4u5-app-menu-link-main:has(a[class='uu5-bricks-link plus4u5-app-menu-icon'])"
        )

        for i in range(items.count()):
            item = items.nth(i)
            # Expand the item
            item.locator("a[class='uu5-bricks-link plus4u5-app-menu-icon']").click()
            item.click()
            item_name = item.text_content()
            page.wait_for_selector(".uu-bookkit-page-ready")
            time.sleep(1)
            # print_pdf(page, item_name)
            print_pdf(page, i + 1)
            sub_items = item.locator("..").locator("div[style='display: block;'] > div")
            for j in range(sub_items.count()):
                sub_item = sub_items.nth(j)
                logger.debug(sub_item.text_content())
                sub_item.click()
                page.wait_for_selector(".uu-bookkit-page-ready")
                time.sleep(1)
                # print_pdf(page, item_name, j + 1)
                print_pdf(page, i + 1, j + 1)
        page.wait_for_timeout(10000)
        browser.close()


if __name__ == "__main__":
    main()
