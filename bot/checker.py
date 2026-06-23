from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from bot.config import (
    FOREIGN_BIRTH_CERT_SUBPRODUCT,
    LOCATIONS,
    Settings,
)

logger = logging.getLogger(__name__)

NEXT_BUTTON = 'input[type="submit"][value="Volgende"], button[value="Volgende"]'
SAMPLE_TIMES_PER_DAY = 3


@dataclass(frozen=True)
class LocationAvailability:
    location: str
    month_label: str
    days: list[str]
    sample_times: dict[str, list[str]]

    def as_dict(self) -> dict[str, str | list[str] | dict[str, list[str]]]:
        return {
            "location": self.location,
            "month_label": self.month_label,
            "days": self.days,
            "sample_times": self.sample_times,
        }


async def click_next(page: Page) -> None:
    button = page.locator(NEXT_BUTTON).first
    await button.wait_for(state="visible", timeout=30_000)
    await button.click()
    await page.wait_for_load_state("networkidle", timeout=60_000)


async def click_hidden_radio(page: Page, value: str) -> None:
    await page.locator(f'input[type="radio"][value="{value}"]').evaluate(
        "el => el.click()"
    )


async def navigate_to_foreign_birth_certificate_form(page: Page, document_count: str) -> None:
    await page.goto(BOOKING_URL, wait_until="domcontentloaded", timeout=60_000)
    await page.locator('input[type="submit"][value="Verder"]').click()
    await page.wait_for_load_state("networkidle", timeout=60_000)

    await click_hidden_radio(page, "Burgerzaken")
    await click_next(page)

    await page.locator('select[id*="ProductenBurgerzaken"]').select_option("Akten")
    await click_next(page)

    await page.locator('select[id*="SubProductenAkten"]').select_option(
        FOREIGN_BIRTH_CERT_SUBPRODUCT
    )
    await click_next(page)

    count_select = page.locator('select[id*="Akten"]')
    if await count_select.count():
        await count_select.first.select_option(document_count)
        await click_next(page)

    await click_hidden_radio(page, "N")
    await click_next(page)


async def read_calendar_month(page: Page) -> str:
    text = await page.locator("body").inner_text()
    match = re.search(
        r"(januari|februari|maart|april|mei|juni|juli|augustus|"
        r"september|oktober|november|december)\s+\d{4}",
        text,
        re.IGNORECASE,
    )
    return match.group(0) if match else "unknown month"


async def open_location_calendar(
    page: Page, location_name: str, location_id: str, document_count: str
) -> str:
    await navigate_to_foreign_birth_certificate_form(page, document_count)

    location_select = page.locator('select[id*="Loketkeuze"]')
    await location_select.wait_for(state="visible", timeout=30_000)
    await location_select.select_option(location_id)
    await click_next(page)

    await page.wait_for_selector('a:has-text("<")', timeout=60_000)
    return await read_calendar_month(page)


async def list_available_days(page: Page) -> list[str]:
    seen: set[str] = set()
    days: list[str] = []
    anchors = page.locator("table a")
    count = await anchors.count()
    for index in range(count):
        anchor = anchors.nth(index)
        text = (await anchor.inner_text()).strip()
        if text.isdigit() and text not in seen:
            seen.add(text)
            days.append(text)
    return days


async def list_times_for_day(page: Page, day: str) -> list[str]:
    day_link = page.locator("table a").filter(has_text=re.compile(rf"^{re.escape(day)}$"))
    if await day_link.count() == 0:
        return []

    await day_link.first.click()
    await page.wait_for_load_state("networkidle", timeout=60_000)

    time_select = page.locator('select[id*="Tijd"]')
    await time_select.wait_for(state="visible", timeout=30_000)

    for _ in range(30):
        options = await time_select.locator("option").all_inner_texts()
        times = [opt.strip() for opt in options if opt.strip() and "keuze" not in opt.lower()]
        if times:
            return times
        await asyncio.sleep(0.5)

    return []


async def check_location(
    page: Page, location_name: str, location_id: str, document_count: str
) -> LocationAvailability | None:
    logger.info("Checking %s", location_name)
    month_label = await open_location_calendar(page, location_name, location_id, document_count)
    days = await list_available_days(page)

    if not days:
        logger.info("No available days at %s", location_name)
        return None

    sample_times: dict[str, list[str]] = {}
    for day in days[:2]:
        times = await list_times_for_day(page, day)
        if times:
            sample_times[day] = times[:SAMPLE_TIMES_PER_DAY]

    logger.info("Found %s available day(s) at %s", len(days), location_name)
    return LocationAvailability(
        location=location_name,
        month_label=month_label,
        days=days,
        sample_times=sample_times,
    )


async def check_all_locations(settings: Settings) -> list[LocationAvailability]:
    from playwright.async_api import async_playwright

    results: list[LocationAvailability] = []

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=settings.headless)
        context = await browser.new_context(locale="nl-NL")
        page = await context.new_page()

        try:
            for location_name, location_id in LOCATIONS.items():
                try:
                    availability = await check_location(
                        page, location_name, location_id, settings.document_count
                    )
                    if availability:
                        results.append(availability)
                except PlaywrightTimeoutError as exc:
                    logger.error("Timeout while checking %s: %s", location_name, exc)
                except Exception:
                    logger.exception("Failed while checking %s", location_name)
        finally:
            await browser.close()

    return results
