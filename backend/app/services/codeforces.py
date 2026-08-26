import asyncio
import logging

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from app.config import settings

CF_BASE = settings.cf_api_base
logger = logging.getLogger("codeforces")


class CodeforcesClient:
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
        )
        self._browser = None
        self._context = None
        self._playwright = None
        self._logged_in = False

    async def login(self, handle_or_email: str, password: str) -> bool:
        """Open a real browser for user to login manually past Cloudflare."""
        try:
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
            )
            self._context = await self._browser.new_context()
            page = await self._context.new_page()
            await page.add_init_script(
                'Object.defineProperty(navigator, "webdriver", { get: () => false });'
            )

            # Navigate to login page — user will solve Cloudflare manually
            await page.goto("https://codeforces.com/enter", timeout=15000)

            # Pre-fill credentials so user just needs to solve captcha and click
            try:
                await page.wait_for_selector("#handleOrEmail", timeout=60000)
                await page.fill("#handleOrEmail", handle_or_email)
                await page.fill("#password", password)
            except Exception:
                pass

            # Wait for user to complete login (up to 2 minutes)
            try:
                await page.wait_for_url(
                    lambda url: "/enter" not in url and "codeforces.com" in url,
                    timeout=120000,
                )
                self._logged_in = True
                logger.info("CF login successful via browser")
                await page.close()
                return True
            except Exception:
                self._logged_in = False
                return False

        except Exception as e:
            logger.warning("CF login error: %s", e)
            self._logged_in = False
            return False

    @property
    def is_logged_in(self) -> bool:
        return self._logged_in

    async def get_user_submissions(self, handle: str, count: int = 300) -> list[dict]:
        url = f"{CF_BASE}/user.status"
        params = {"handle": handle, "from": 1, "count": count}
        resp = await self.client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

        if data["status"] != "OK":
            raise ValueError(f"CF API error: {data.get('comment', 'unknown')}")

        return data["result"]

    async def get_submission_source(self, contest_id: int, submission_id: int) -> str | None:
        """Fetch source code using the authenticated browser session."""
        if not self._context:
            return None

        try:
            page = await self._context.new_page()
            url = f"https://codeforces.com/contest/{contest_id}/submission/{submission_id}"
            await page.goto(url, timeout=20000)

            # Wait for page to load (might have Cloudflare but session should pass)
            try:
                await page.wait_for_selector("#program-source-text", timeout=15000)
            except Exception:
                await page.close()
                return None

            source_elem = await page.query_selector("#program-source-text")
            if source_elem:
                source = await source_elem.inner_text()
                await page.close()
                return source

            await page.close()
            return None

        except Exception as e:
            logger.warning("Source fetch failed for %d/%d: %s", contest_id, submission_id, e)
            return None

    async def get_user_info(self, handle: str) -> dict | None:
        url = f"{CF_BASE}/user.info"
        params = {"handles": handle}
        resp = await self.client.get(url, params=params)
        if resp.status_code != 200:
            return None

        data = resp.json()
        if data["status"] == "OK" and data["result"]:
            return data["result"][0]
        return None

    def filter_accepted_cpp(self, submissions: list[dict]) -> list[dict]:
        return [
            s for s in submissions
            if s.get("verdict") == "OK"
            and "C++" in s.get("programmingLanguage", "")
        ]

    async def close(self):
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        await self.client.aclose()


cf_client = CodeforcesClient()
