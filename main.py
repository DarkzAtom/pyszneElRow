import asyncio
import random
import re
import time
from undetected_playwright.async_api import async_playwright, expect, Playwright
from playwright_stealth import stealth_async, StealthConfig
import json
import logging
from tgnotif import main as send_tg_notif
from datetime import date


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


async def setup_browser_context(playwright):
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.2045.43 Safari/537.36 Edg/117.0.2045.43',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.1938.69 Safari/537.36 Edg/116.0.1938.69',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.1901.203 Safari/537.36 Edg/115.0.1901.203',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.1823.67 Safari/537.36 Edg/114.0.1823.67',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.62 Safari/537.36 OPR/101.0.4843.33',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.111 Safari/537.36 OPR/100.0.4815.30',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.5790.110 Safari/537.36 OPR/99.0.4788.87',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.198 Safari/537.36 OPR/98.0.4759.39',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.93 Safari/537.36 OPR/97.0.4719.63',
    ]

    user_agent = random.choice(user_agents)
    print(f'USER-AGENT selected: {user_agent}')

    browser = await playwright.chromium.launch(
        channel='chrome',
        headless=True,
        slow_mo=435,
        args=[
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled',
            '--disable-extensions',
            '--disable-infobars',
            '--disable-backgrounding-occluded-windows',
            '--disable-gpu',
            '--disable-software-rasterizer',
            '--ignore-certificate-errors',
            '--disable-popup-blocking',
            '--disable-notifications',
            '--disable-browser-side-navigation',
        ]
    )

    context = await browser.new_context(
        locale='pl-PL',
        user_agent=user_agent,
        no_viewport=True,
        ignore_https_errors=True,
    )


    await context.add_init_script("""
        delete window.__proto__.webdriver;
    """)


    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)

    return browser, context


list_of_cities: list = []
citieslist_withrower: list = []


async def go_back_to_cities(page):
    await page.go_back()
    await page.wait_for_load_state('networkidle')
    droppill_cities = page.locator('div.dropdown_pill').nth(0)
    await droppill_cities.click()
    await page.wait_for_timeout(230)
    await page.wait_for_load_state('networkidle')


async def run_task(playwright: Playwright):
    browser, context = await setup_browser_context(playwright)
    page = await context.new_page()
    config = StealthConfig(navigator_languages=False, navigator_vendor=False, navigator_user_agent=False)
    await stealth_async(page, config)
    try:
        await page.goto('https://www.pyszne.pl/kurier')
        await page.wait_for_load_state('networkidle')
        deny_cookies = page.get_by_text('Zaakceptuj wszystkie')
        await deny_cookies.click()
        droppill_cities = page.locator('div.dropdown_pill').nth(0)
        await droppill_cities.click()
        box_with_cities = page.locator('div.salary_dropdown_results_container').nth(0)
        cities = box_with_cities.locator('div')
        for city in await cities.all():
            city_text = await city.text_content()
            city_rfnd = city_text.strip()
            list_of_cities.append(city_rfnd)
        print('the cities we will look at for today are:')
        for city in list_of_cities:
            print(city)
        for index, city in enumerate(list_of_cities):
            box_with_cities = page.locator('div.salary_dropdown_results_container').nth(0)
            city_to_prcd = box_with_cities.get_by_text(city).nth(0)
            await city_to_prcd.click()
            await page.wait_for_timeout(1000)
            apply_btn = page.locator('button#application_button')
            await apply_btn.scroll_into_view_if_needed()
            await apply_btn.click()
            await page.wait_for_load_state('networkidle')
            pelnoletni_btn = page.locator('input[name="age"]').locator('..').locator('div').nth(0)
            await pelnoletni_btn.scroll_into_view_if_needed()
            await pelnoletni_btn.click()
            firmowy_rower_element = page.get_by_text(re.compile(r'Firmowy (e-)?rower'))
            try:
                await expect(firmowy_rower_element).to_be_visible(timeout=2500)
                print(f'{city}: there is such an element hooray!!!!')
                citieslist_withrower.append(city)
                time.sleep(3.5)
                await go_back_to_cities(page)
            except Exception as e:
                logger.error(f"{city}: Can't find an element: {e}")
                time.sleep(1)
                await go_back_to_cities(page)
            await page.wait_for_timeout(1500)
            await page.wait_for_load_state('networkidle')
        logger.info('FINAL list of cities with rower:')
        for city in citieslist_withrower:
            print(city)
        time.sleep(7)
    except Exception as e:
        logger.error(f'error running webinstance: {e}')
    finally:
        await browser.close()

    # if "Poznaniu" in citieslist_withrower or "Poznań" in citieslist_withrower:
    #     send_tg_notif()
    #     with open('registry.txt', 'a') as file:
    #         file.write(f'{date.today()}: There are e-bikes available in Poznan-Pyszne.')
    # else:
    #     with open('registry.txt', 'a') as file:
    #         file.write(f'{date.today()}: No e-bikes in Poznan-Pyszne.')






async def main():
    async with async_playwright() as playwright:
        await run_task(playwright)


if __name__ == "__main__":
    asyncio.run(main())