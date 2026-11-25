"""UI tests for https://www.iamdave.ai using Playwright (sync API) + pytest.

Run:  pytest tests/ui_tests.py --headed      (omit --headed for headless)
Note: the site can change. If a test fails on a selector, open the site,
inspect the element and adjust the locator.
"""
import re
from urllib.parse import urljoin, urlparse

import pytest
from playwright.sync_api import Page, expect, sync_playwright

URL = "https://www.iamdave.ai"


@pytest.fixture(scope="module")
def browser():
    """SETUP: launch Chromium once. TEARDOWN: close it after all tests."""
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        yield b
        b.close()


@pytest.fixture
def page(browser):
    """SETUP: fresh isolated browser context + page for every test.
    TEARDOWN: context closed, so no cookies/state leak between tests."""
    ctx = browser.new_context(viewport={"width": 1366, "height": 768})
    pg = ctx.new_page()
    pg.set_default_timeout(20000)
    yield pg
    ctx.close()


def test_homepage_loads_with_title(page: Page):
    """Site loads (HTTP < 400) and the title mentions the brand."""
    resp = page.goto(URL, wait_until="domcontentloaded")
    assert resp is not None and resp.status < 400
    expect(page).to_have_title(re.compile("dave", re.IGNORECASE))


def test_main_heading_visible(page: Page):
    """Homepage shows at least one visible, non-empty top-level heading."""
    page.goto(URL, wait_until="domcontentloaded")
    heading = page.locator("h1").first
    expect(heading).to_be_visible()
    assert heading.inner_text().strip() != ""


def test_navigation_links_present(page: Page):
    """Header/navigation has several links, and at least one logo image exists."""
    page.goto(URL, wait_until="domcontentloaded")
    nav_links = page.locator("header a, nav a")
    assert nav_links.count() >= 3
    assert page.locator("img").count() >= 1


def test_navigation_flow_opens_new_page(page: Page):
    """Click internal nav links (up to 5 candidates) until one opens a different
    page or a new tab. Links that just reload the homepage (e.g. a 'Home' link)
    are skipped, so the test does not depend on which link renders first."""
    page.goto(URL, wait_until="domcontentloaded")
    links = page.locator("header a[href], nav a[href]")
    candidates = []  # (raw_href, full_url)
    for i in range(links.count()):
        link = links.nth(i)
        raw = (link.get_attribute("href") or "").strip()
        parsed = urlparse(urljoin(URL + "/", raw))
        if (parsed.netloc.endswith("iamdave.ai") and parsed.path not in ("", "/")
                and not parsed.fragment and not raw.startswith(("mailto:", "tel:"))
                and "home" not in parsed.path.lower() and link.is_visible()
                and all(raw != c[0] for c in candidates)):
            candidates.append((raw, parsed.geturl()))
    if not candidates:
        pytest.skip("No visible internal navigation link found; update locator")

    tried = []
    for raw, full in candidates[:5]:
        page.goto(URL, wait_until="domcontentloaded")
        link = page.locator(f'header a[href="{raw}"], nav a[href="{raw}"]').first
        if not link.is_visible():
            continue
        pages_before = len(page.context.pages)
        link.click()
        page.wait_for_timeout(3000)
        new_tab = len(page.context.pages) > pages_before
        current = page.context.pages[-1] if new_tab else page
        current.wait_for_load_state("domcontentloaded")
        tried.append(full)
        if new_tab or urlparse(current.url).path.strip("/") != "":
            expect(current.locator("body")).to_be_visible()
            return  # navigation verified
    pytest.fail(f"No nav link navigated away from the homepage. Tried: {tried}")


    def test_contact_form_input(page: Page):
        page.goto(
        "https://www.iamdave.ai/contact-us/",
        wait_until="domcontentloaded"
    )

    inputs = page.locator("input:visible")

    # Verify that contact form inputs are available
    expect(inputs.first).to_be_visible()
    assert inputs.count() >= 4

    # Enter sample data without submitting the form
    inputs.nth(0).fill("Test User")
    inputs.nth(1).fill("test@example.com")

    # Verify entered values
    expect(inputs.nth(0)).to_have_value("Test User")
    expect(inputs.nth(1)).to_have_value("test@example.com")


    def test_contact_form_button(page: Page):
        page.goto(
        "https://www.iamdave.ai/contact-us/",
        wait_until="domcontentloaded"
    )

    buttons = page.locator(
        "button:visible, input[type='submit']:visible"
    )

    assert buttons.count() > 0