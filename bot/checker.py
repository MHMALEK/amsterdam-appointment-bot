from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import date, datetime

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from bot.config import BOOKING_URL, FOREIGN_BIRTH_CERT_SUBPRODUCT, LOCATIONS, Settings
from bot.dates import (
    calendar_grid_dates,
    month_label_for_date,
    parse_month_label,
    slot_datetime_from_date,
)

logger = logging.getLogger(__name__)

NEXT_BUTTON = 'input[type="submit"][value="Volgende"], button[value="Volgende"]'


@dataclass(frozen=True, order=True)
class AppointmentSlot:
    when: datetime
    location: str
    month_label: str
    day: str
    time: str


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
    header = page.locator("table.appointmentControlCalendar td[align='center']")
    if await header.count() > 0:
        text = (await header.first.inner_text()).strip()
        if text:
            return text

    text = await page.locator("body").inner_text()
    match = re.search(
        r"(januari|februari|maart|april|mei|juni|juli|augustus|"
        r"september|oktober|november|december)\s+\d{4}",
        text,
        re.IGNORECASE,
    )
    return match.group(0) if match else "unknown month"


async def navigate_to_calendar_month(page: Page, target_year: int, target_month: int) -> None:
    for _ in range(24):
        label = await read_calendar_month(page)
        year, month = parse_month_label(label)
        if year == target_year and month == target_month:
            return

        current = date(year, month, 1)
        target = date(target_year, target_month, 1)
        if current < target:
            if not await click_calendar_next(page):
                break
        elif not await click_calendar_prev(page):
            break

    label = await read_calendar_month(page)
    year, month = parse_month_label(label)
    if year != target_year or month != target_month:
        raise RuntimeError(
            f"Could not navigate calendar to {target_year}-{target_month:02d} (at {label})"
        )


_CALENDAR_LINK_INDICES_JS = """() => {
    const calendarTable = document.querySelector("table.appointmentControlCalendar");
    const outerTable = calendarTable
        ? calendarTable.closest("table")
        : document.querySelector("table");
    const rows = Array.from(outerTable.querySelectorAll("tbody tr"));
    const indices = [];
    let gridRow = 0;

    for (const row of rows) {
        if (row.querySelectorAll("th").length === 7) {
            gridRow = 0;
            continue;
        }
        const tds = row.querySelectorAll("td");
        if (tds.length !== 7) {
            continue;
        }
        for (let col = 0; col < 7; col++) {
            const td = tds[col];
            const link = td.querySelector("a");
            if (link && /^\\d+$/.test(td.innerText.trim())) {
                indices.push(gridRow * 7 + col);
            }
        }
        gridRow++;
    }

    return indices;
}"""


async def _calendar_link_indices(page: Page) -> list[int]:
    return await page.evaluate(_CALENDAR_LINK_INDICES_JS)


async def click_calendar_date(page: Page, month_label: str, slot_date: date) -> bool:
    year, month = parse_month_label(month_label)
    grid_dates = calendar_grid_dates(year, month)
    try:
        index = grid_dates.index(slot_date)
    except ValueError:
        return False

    return await page.evaluate(
        """(cellIndex) => {
            const calendarTable = document.querySelector("table.appointmentControlCalendar");
            const outerTable = calendarTable
                ? calendarTable.closest("table")
                : document.querySelector("table");
            const rows = Array.from(outerTable.querySelectorAll("tbody tr"));
            let current = 0;

            for (const row of rows) {
                if (row.querySelectorAll("th").length === 7) {
                    continue;
                }
                const tds = row.querySelectorAll("td");
                if (tds.length !== 7) {
                    continue;
                }
                for (let col = 0; col < 7; col++) {
                    if (current === cellIndex) {
                        const link = tds[col].querySelector("a");
                        if (!link) {
                            return false;
                        }
                        link.click();
                        return true;
                    }
                    current++;
                }
            }

            return false;
        }""",
        index,
    )


async def open_location_calendar(
    page: Page, location_name: str, location_id: str, document_count: str
) -> None:
    await navigate_to_foreign_birth_certificate_form(page, document_count)

    location_select = page.locator('select[id*="Loketkeuze"]')
    await location_select.wait_for(state="visible", timeout=30_000)
    await location_select.select_option(location_id)
    await click_next(page)
    await page.wait_for_selector('a:has-text("<")', timeout=60_000)


async def list_available_dates(page: Page, month_label: str) -> list[date]:
    year, month = parse_month_label(month_label)
    grid_dates = calendar_grid_dates(year, month)
    indices = await _calendar_link_indices(page)
    return [grid_dates[index] for index in indices if 0 <= index < len(grid_dates)]


async def list_times_for_date(page: Page, month_label: str, slot_date: date) -> list[str]:
    if not await click_calendar_date(page, month_label, slot_date):
        return []

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


def qualifying_dates(
    available_dates: list[date], deadline: date, today: date
) -> list[date]:
    result: list[date] = []
    for slot_date in available_dates:
        if slot_date >= deadline or slot_date < today:
            continue
        result.append(slot_date)
    return result


async def click_calendar_prev(page: Page) -> bool:
    prev = page.locator("table").locator("a").filter(has_text="<")
    if await prev.count() == 0:
        return False
    await prev.first.click()
    await page.wait_for_load_state("networkidle", timeout=60_000)
    return True


async def click_calendar_next(page: Page) -> bool:
    nxt = page.locator("table").locator("a").filter(has_text=">")
    if await nxt.count() == 0:
        return False
    await nxt.first.click()
    await page.wait_for_load_state("networkidle", timeout=60_000)
    return True


async def collect_qualifying_date_keys(
    page: Page, deadline: date, today: date
) -> list[tuple[str, date]]:
    # Walk back up to 6 months, then forward until past the deadline month.
    for _ in range(6):
        month_label = await read_calendar_month(page)
        year, month = parse_month_label(month_label)
        if date(year, month, 1) <= date(today.year, today.month, 1):
            break
        if not await click_calendar_prev(page):
            break

    seen: set[date] = set()
    ordered: list[tuple[str, date]] = []

    for _ in range(12):
        month_label = await read_calendar_month(page)
        year, month = parse_month_label(month_label)
        if date(year, month, 1) > deadline.replace(day=1):
            break

        for slot_date in qualifying_dates(
            await list_available_dates(page, month_label), deadline, today
        ):
            if slot_date in seen:
                continue
            seen.add(slot_date)
            ordered.append((month_label, slot_date))

        if date(year, month, 1) >= deadline.replace(day=1):
            break
        if not await click_calendar_next(page):
            break

    return ordered


async def check_location(
    page: Page,
    location_name: str,
    location_id: str,
    document_count: str,
    deadline: date,
    today: date,
) -> list[AppointmentSlot]:
    logger.info("Checking %s", location_name)
    await open_location_calendar(page, location_name, location_id, document_count)

    date_keys = await collect_qualifying_date_keys(page, deadline, today)
    if not date_keys:
        logger.info("No qualifying days before %s at %s", deadline, location_name)
        return []

    slots: list[AppointmentSlot] = []
    for month_label, slot_date in date_keys:
        view_year, view_month = parse_month_label(month_label)
        await navigate_to_calendar_month(page, view_year, view_month)
        times = await list_times_for_date(page, month_label, slot_date)
        for time in times:
            when = slot_datetime_from_date(slot_date, time)
            if when.date() >= deadline or when.date() < today:
                continue
            slots.append(
                AppointmentSlot(
                    when=when,
                    location=location_name,
                    month_label=month_label_for_date(slot_date),
                    day=str(slot_date.day),
                    time=time,
                )
            )

    logger.info("Found %s slot(s) before deadline at %s", len(slots), location_name)
    return slots


async def check_all_locations(settings: Settings) -> list[AppointmentSlot]:
    from playwright.async_api import async_playwright

    today = date.today()
    all_slots: list[AppointmentSlot] = []

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=settings.headless)
        context = await browser.new_context(locale="nl-NL")
        page = await context.new_page()

        try:
            for location_name, location_id in LOCATIONS.items():
                try:
                    slots = await check_location(
                        page,
                        location_name,
                        location_id,
                        settings.document_count,
                        settings.deadline,
                        today,
                    )
                    all_slots.extend(slots)
                except PlaywrightTimeoutError as exc:
                    logger.error("Timeout while checking %s: %s", location_name, exc)
                except Exception:
                    logger.exception("Failed while checking %s", location_name)
        finally:
            await browser.close()

    return all_slots
