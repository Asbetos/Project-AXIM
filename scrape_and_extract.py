"""
scrape_and_extract.py — Automated Browser Scraping + Claude Extraction (v4)

WHAT'S NEW in v4:
  - Auto-discovers all school URLs from the rankings table page (ranks 1-120)
  - Expands all 7 collapsible sections on each school profile
  - Extracts only the metrics region (no nav, ads, or footer noise)

Usage:
  python scrape_and_extract.py                  # Scrape + extract (uses existing schools.csv)
  python scrape_and_extract.py --login          # Force fresh login first
  python scrape_and_extract.py --scrape-only    # Scrape text files only, no API calls
  python scrape_and_extract.py --discover       # Re-discover school URLs from rankings table

Prerequisites:
  pip install anthropic playwright python-dotenv
  playwright install chromium
"""

import csv
import os
import random
import re
import sys
import time
import json
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    raise ImportError("Run: pip install playwright && playwright install chromium")

from core_extractor import load_prompt, extract_school_data, save_json


# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
SCHOOLS_CSV = "schools.csv"
OUTPUT_DIR = Path("output_json")
PAGE_TEXTS_DIR = Path("page_texts")
BROWSER_PROFILE_DIR = Path("browser_profile")  # Persistent profile
DELAY_BETWEEN_PAGES = 5

RANKINGS_TABLE_URL = (
    "https://premium.usnews.com/best-graduate-schools/"
    "top-business-schools/mba-rankings?_mode=table"
)
NOMINAL_RANK_COUNT = (
    122  # Exact-number-ranked schools before range-ranked entries begin
)
EXPECTED_EXPAND_SECTIONS = 7  # SEE MORE buttons + AND X MORE on each profile

# Domains to block at the network level.  These serve ads, tracking pixels,
# and interstitial overlays that interfere with automated page interaction.
AD_BLOCK_DOMAINS = [
    # Google ads & tracking
    "doubleclick.net",
    "googlesyndication.com",
    "googleadservices.com",
    "google-analytics.com",
    "googletagmanager.com",
    "adservice.google.com",
    "pagead2.googlesyndication.com",
    "tpc.googlesyndication.com",
    "googletagservices.com",
    "gstatic.com/adsense",
    # Facebook
    "facebook.net",
    "connect.facebook.net",
    "facebook.com/tr",
    # Amazon
    "amazon-adsystem.com",
    "aax.amazon-adsystem.com",
    # Major ad exchanges
    "adnxs.com",
    "ib.adnxs.com",
    "adsrvr.org",
    "rubiconproject.com",
    "pubmatic.com",
    "casalemedia.com",
    "openx.net",
    "smartadserver.com",
    "serving-sys.com",
    "contextweb.com",
    "yieldmo.com",
    "sharethrough.com",
    "indexexchange.com",
    "33across.com",
    "media.net",
    # Content recommendation (Taboola / Outbrain / etc)
    "taboola.com",
    "outbrain.com",
    "outbrainimg.com",
    "zergnet.com",
    "revcontent.com",
    "mgid.com",
    # Tracking & analytics
    "criteo.com",
    "criteo.net",
    "moatads.com",
    "quantserve.com",
    "scorecardresearch.com",
    "sb.scorecardresearch.com",
    "bluekai.com",
    "demdex.com",
    "krxd.net",
    "cdn.permutive.com",
    "bat.bing.com",
    "ads.linkedin.com",
    "bidswitch.net",
    "rlcdn.com",
    "mathtag.com",
    "dotomi.com",
    "adsymptotic.com",
    "chartbeat.com",
    "newrelic.com",
    "nr-data.net",
    # US News specific ad partners (common on news sites)
    "securepubads.g.doubleclick.net",
    "ad.doubleclick.net",
    "cm.g.doubleclick.net",
    "stats.g.doubleclick.net",
    "connatix.com",
    "1rx.io",
    "yldbt.com",
    "bidsxchange.com",
    "liadm.com",
    "lijit.com",
    "sonobi.com",
    "spotxchange.com",
]


# ---------------------------------------------------------------------------
# BROWSER LAUNCH — uses real Chrome/Edge to avoid detection
# ---------------------------------------------------------------------------


def _abort_route(route):
    """Route handler that blocks a request."""
    route.abort()


def launch_browser(pw):
    """
    Launch a persistent browser context using the real installed browser.
    This avoids bot detection because it's the actual Chrome/Edge binary,
    not Playwright's bundled Chromium (which sites can fingerprint).

    Ad blocking is NOT enabled here — it must be enabled after login
    so the login/auth overlay can load normally.  Call enable_ad_blocking()
    on the returned context after the user is logged in.
    """
    BROWSER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    profile_path = str(BROWSER_PROFILE_DIR.resolve())

    # Try using the user's installed Chrome or Edge
    for channel in ["chrome", "msedge", None]:
        try:
            channel_name = channel or "chromium (bundled)"
            print(f"  Trying to launch: {channel_name}...")

            context = pw.chromium.launch_persistent_context(
                user_data_dir=profile_path,
                channel=channel,  # None = use bundled Chromium as fallback
                headless=False,
                viewport={"width": 1400, "height": 900},
                args=[
                    "--disable-blink-features=AutomationControlled",  # Hide automation
                ],
                ignore_default_args=["--enable-automation"],  # Hide automation bar
            )

            # --- Stealth + ad nuking init script ---
            # Runs before every page's own JS:
            #   1. Hides navigator.webdriver
            #   2. Blocks window.open() so ads can't spawn new tabs
            #   3. Removes ad iframes and common ad containers from the DOM
            context.add_init_script("""
                // Hide automation
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                window.cdc_adoQpoasnfa76pfcZLmcfl_Array = undefined;
                window.cdc_adoQpoasnfa76pfcZLmcfl_Promise = undefined;
                window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol = undefined;

                // Block window.open (prevents ad popups / new tabs)
                window.open = function() { return null; };
            """)

            # --- Auto-close any new tab that somehow still opens ---
            def _close_new_page(new_page):
                try:
                    new_page.close()
                except Exception:
                    pass

            context.on("page", _close_new_page)

            print(f"  [OK] Launched: {channel_name}")
            return context

        except Exception as e:
            print(f"  [X] {channel_name} failed: {e}")
            continue

    print("\n[X] Could not launch any browser.")
    print(
        "  Make sure Chrome or Edge is installed, or run: playwright install chromium"
    )
    sys.exit(1)


def enable_ad_blocking(context):
    """Enable network-level ad blocking on the browser context.

    Must be called AFTER login — the login/auth overlay depends on
    third-party domains (e.g. Google, Facebook sign-in) that would
    be blocked otherwise.
    """
    for domain in AD_BLOCK_DOMAINS:
        context.route(f"**/*{domain}*", _abort_route)
    print(f"  [OK] Ad blocking enabled ({len(AD_BLOCK_DOMAINS)} domains)")


def strip_ad_elements(page):
    """Remove ad iframes, ad containers, and sponsored content from the DOM.

    Network-level blocking stops new ad requests, but ad HTML/iframes
    that were already in the page (or served inline) remain clickable.
    This removes them so automated clicks can't accidentally hit ads.
    """
    removed = page.evaluate("""
        () => {
            let removed = 0;

            // 1. Remove all iframes (ads are almost always in iframes)
            for (const el of document.querySelectorAll('iframe')) {
                el.remove();
                removed++;
            }

            // 2. Remove elements with ad-related class/id patterns
            const adSelectors = [
                '[id*="google_ads"]', '[id*="gpt-ad"]', '[id*="ad-slot"]',
                '[id*="ad_slot"]', '[id*="AdSlot"]', '[id*="advertisement"]',
                '[class*="ad-container"]', '[class*="ad-slot"]',
                '[class*="ad-wrapper"]', '[class*="ad_wrapper"]',
                '[class*="advertisement"]', '[class*="sponsored"]',
                '[class*="taboola"]', '[class*="outbrain"]',
                '[class*="connatix"]', '[class*="zergnet"]',
                '[data-google-query-id]', '[data-ad-slot]',
                'ins.adsbygoogle',
            ];
            for (const sel of adSelectors) {
                for (const el of document.querySelectorAll(sel)) {
                    el.remove();
                    removed++;
                }
            }

            // 3. Remove any remaining fixed/absolute positioned iframes
            //    or small fixed banners (cookie bars already handled elsewhere)
            for (const el of document.querySelectorAll('[style*="position: fixed"], [style*="position:fixed"]')) {
                const tag = el.tagName.toLowerCase();
                if (tag === 'iframe') {
                    el.remove();
                    removed++;
                }
            }

            return removed;
        }
    """)
    if removed:
        print(f"  Stripped {removed} ad element(s) from DOM")


# ---------------------------------------------------------------------------
# LOGIN
# ---------------------------------------------------------------------------


def check_and_login(page, force_login=False):
    """
    Navigate to a school page to test access.
    If not logged in, pause for manual login.
    """
    if force_login:
        print("\n  Force login requested — opening US News...")
        safe_goto(
            page,
            "https://www.usnews.com/best-graduate-schools/top-business-schools/mba-rankings",
        )
        print()
        print("  " + "=" * 56)
        print("  PLEASE LOG IN")
        print("  " + "=" * 56)
        print("  1. Click 'Sign In' in the browser window")
        print("  2. Log into your US News premium account")
        print("  3. Come back here and press Enter")
        print()
        input("  >>> Press Enter after you're logged in... ")
        return

    # Test by visiting a non-premium page first (less likely to block)
    print("\n  Checking if logged in...")
    safe_goto(
        page,
        "https://www.usnews.com/best-graduate-schools/top-business-schools/mba-rankings",
    )
    time.sleep(3)

    # Now try a premium URL
    safe_goto(
        page,
        "https://premium.usnews.com/best-graduate-schools/top-business-schools/university-of-pennsylvania-01194",
    )
    time.sleep(4)

    page_text = safe_get_text(page)[:3000].lower()
    current_url = page.url.lower()

    # Heuristics for "logged in and have premium access"
    has_content = any(
        kw in page_text
        for kw in [
            "wharton",
            "acceptance rate",
            "average base salary",
            "overall score",
            "peer assessment",
            "gmat",
        ]
    )

    if has_content and "premium.usnews.com" in current_url:
        print("  [OK] Logged in with premium access!")
        return

    # Not logged in
    print()
    print("  " + "=" * 56)
    print("  LOGIN NEEDED")
    print("  " + "=" * 56)
    print()
    print("  The browser is open. Please:")
    print("  1. Navigate to usnews.com and click 'Sign In'")
    print("  2. Log into your premium account")
    print("  3. Verify you can see school data (not a paywall)")
    print("  4. Come back here and press Enter")
    print()
    input("  >>> Press Enter when you're logged in and can see school data... ")


# ---------------------------------------------------------------------------
# SAFE NAVIGATION HELPERS
# ---------------------------------------------------------------------------


def safe_goto(page, url, timeout=45000):
    """Navigate to a URL, handling common errors gracefully."""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        return True
    except Exception as e:
        error_msg = str(e).lower()
        if "err_http2" in error_msg or "protocol" in error_msg:
            # HTTP/2 error — try again with a delay
            print(f"  [!] Connection blocked, retrying in 5s...")
            time.sleep(5)
            try:
                page.goto(url, timeout=timeout)
                return True
            except Exception:
                print(f"  [!] Still blocked. Trying non-premium URL...")
                # Try the non-premium version
                alt_url = url.replace("premium.usnews.com", "www.usnews.com")
                try:
                    page.goto(alt_url, timeout=timeout)
                    return True
                except Exception:
                    pass
        elif "timeout" in error_msg:
            print(f"  [!] Page load timed out; continuing with partial content")
            return True  # Page may have partially loaded
        else:
            print(f"  [!] Navigation error: {e}")

        return False


def safe_get_text(page) -> str:
    """Get page text safely."""
    try:
        return page.locator("body").inner_text(timeout=10000)
    except Exception:
        try:
            return page.content()
        except Exception:
            return ""


def scroll_full_page(page):
    """Scroll through the entire page viewport-by-viewport to trigger lazy loading."""
    try:
        page.evaluate("""
            (async () => {
                const step = window.innerHeight;
                const maxScroll = document.body.scrollHeight;
                for (let y = 0; y <= maxScroll; y += step) {
                    window.scrollTo(0, y);
                    await new Promise(r => setTimeout(r, 300));
                }
                window.scrollTo(0, 0);
            })()
        """)
        time.sleep(2)
    except Exception:
        try:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(1)
        except Exception:
            pass


def dismiss_overlay(page):
    """Detect and hide any full-screen anti-bot overlay / image blocker.

    US News shows a full-screen image after detecting automated clicks.
    Instead of removing elements (which can break React's DOM tree),
    this HIDES them with display:none, which is safely reversible and
    doesn't destroy the page structure.

    Uses very strict criteria to avoid hiding legitimate content:
      - Must be fixed/absolute positioned
      - Must cover > 95% of the viewport
      - Must have z-index > 900 (normal content rarely exceeds this)
      - OR must be a full-viewport <img> element
    """
    try:
        page.keyboard.press("Escape")
        time.sleep(0.3)
    except Exception:
        pass

    try:
        hidden = page.evaluate("""
            () => {
                let hidden = 0;
                const vw = window.innerWidth;
                const vh = window.innerHeight;

                for (const el of document.querySelectorAll('*')) {
                    if (el.style.display === 'none') continue;

                    const s = window.getComputedStyle(el);
                    const pos = s.position;
                    if (pos !== 'fixed' && pos !== 'absolute') continue;

                    const w = el.offsetWidth;
                    const h = el.offsetHeight;
                    const z = parseInt(s.zIndex) || 0;

                    // Full-viewport image (the specific anti-bot blocker)
                    if (el.tagName === 'IMG' && w > vw * 0.9 && h > vh * 0.9) {
                        el.style.display = 'none';
                        hidden++;
                        continue;
                    }

                    // Very high z-index overlay covering the full viewport
                    if (z > 900 && w > vw * 0.95 && h > vh * 0.95) {
                        el.style.display = 'none';
                        hidden++;
                    }
                }

                // Re-enable scrolling
                document.body.style.overflow = '';
                document.documentElement.style.overflow = '';

                return hidden;
            }
        """)
        if hidden:
            print(f"  [!] Dismissed {hidden} overlay element(s)")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# DISCOVER SCHOOLS FROM RANKINGS TABLE
# ---------------------------------------------------------------------------


def discover_schools_from_rankings(page) -> list[dict]:
    """
    Navigate to the rankings table page and collect school profile URLs
    for all nominally-ranked schools (ranks #1 through #120).

    Scrolls incrementally until enough school links are loaded,
    then extracts unique profile URLs in table order.
    """
    print(f"\n{'=' * 60}")
    print("Phase 1: Discovering school URLs from rankings table")
    print(f"{'=' * 60}")
    print(f"  Target: all schools with an exact numeric rank")

    if not safe_goto(page, RANKINGS_TABLE_URL):
        print("  [X] Could not load rankings table page.")
        print("  Please navigate to the rankings page manually in the browser.")
        input("  Press Enter when the page has loaded... ")

    time.sleep(5)

    # The rankings table shows a limited batch of schools at a time.
    # We scroll only until the first 122 school profile rows are loaded,
    # which is the exact-ranked cutoff before range-ranked entries begin.
    print("  Loading all ranked schools (scrolling + clicking 'Load More')...")

    count_loaded_schools_js = r"""
        () => {
            const links = document.querySelectorAll(
                'a[href*="/best-graduate-schools/top-business-schools/"]'
            );
            const slugs = new Set();
            for (const a of links) {
                const rawHref = a.getAttribute('href') || '';
                if (!rawHref) continue;

                let path = rawHref;
                try {
                    path = new URL(rawHref, window.location.origin).pathname;
                } catch (e) {}

                path = path.replace(/\/$/, '');
                if (/\/mba-rankings$/i.test(path)) continue;
                if (/\/best-graduate-schools\/top-business-schools\/[^/]+-\d+$/i.test(path)) {
                    slugs.add(path);
                }
            }
            return slugs.size;
        }
    """

    click_load_more_js = r"""
        () => {
            const elements = Array.from(
                document.querySelectorAll('a, button, [role="button"]')
            );
            const candidates = elements.filter((el) => {
                const txt = (el.textContent || '').trim();
                if (!/load more|show more|view more/i.test(txt)) return false;
                if (el.offsetParent === null) return false;
                if (el.disabled || el.getAttribute('aria-disabled') === 'true') return false;
                return true;
            });

            const target = candidates[candidates.length - 1];
            if (!target) return false;

            target.scrollIntoView({behavior: 'smooth', block: 'center'});
            target.click();
            return true;
        }
    """

    pager_state_js = r"""
        () => {
            const elements = Array.from(
                document.querySelectorAll('a, button, [role="button"]')
            );
            let hasVisiblePager = false;

            for (const el of elements) {
                const txt = (el.textContent || '').trim();
                if (!/load more|show more|view more|loading/i.test(txt)) continue;
                if (el.offsetParent === null) continue;
                hasVisiblePager = true;

                if (/loading/i.test(txt)) {
                    return {state: 'loading', text: txt, hasVisiblePager: true};
                }
            }

            return {state: 'idle', text: '', hasVisiblePager};
        }
    """

    stagnant_attempts = 0
    for attempt in range(100):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)

        unique_count = page.evaluate(count_loaded_schools_js)

        if attempt % 2 == 0:
            print(f"    ... {unique_count} schools loaded (attempt {attempt + 1})")

        if unique_count >= NOMINAL_RANK_COUNT:
            print(
                f"    [OK] Reached {unique_count} loaded schools; stopping at threshold"
            )
            break

        pager_state = page.evaluate(pager_state_js)
        if pager_state.get("state") == "loading":
            time.sleep(4)
            continue

        clicked_load_more = page.evaluate(click_load_more_js)
        if clicked_load_more:
            grew = False
            for _ in range(12):
                time.sleep(1)
                new_count = page.evaluate(count_loaded_schools_js)
                if new_count > unique_count:
                    stagnant_attempts = 0
                    grew = True
                    break
            if grew:
                continue
        else:
            time.sleep(2)

        new_count = page.evaluate(count_loaded_schools_js)
        if new_count > unique_count:
            stagnant_attempts = 0
            continue

        stagnant_attempts += 1
        pager_state = page.evaluate(pager_state_js)
        if stagnant_attempts >= 8 and not pager_state.get("hasVisiblePager"):
            print(f"    No more schools to load ({new_count} total)")
            break

    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(1)

    extracted_rows = page.evaluate(
        r"""
        () => {
            const links = Array.from(
                document.querySelectorAll(
                    'a[href*="/best-graduate-schools/top-business-schools/"]'
                )
            );
            const rowsByHref = new Map();

            for (const link of links) {
                const rawHref = link.getAttribute('href') || '';
                if (!rawHref) continue;

                let path = rawHref;
                try {
                    path = new URL(rawHref, window.location.origin).pathname;
                } catch (e) {}

                path = path.replace(/\/$/, '');
                if (/\/mba-rankings$/i.test(path)) continue;
                if (!/\/best-graduate-schools\/top-business-schools\/[^/]+-\d+$/i.test(path)) {
                    continue;
                }
                let container = link;
                let rowText = (link.innerText || '').replace(/\s+/g, ' ').trim();
                for (let i = 0; i < 10 && container; i++) {
                    container = container.parentElement;
                    if (!container) break;
                    const text = (container.innerText || '').replace(/\s+/g, ' ').trim();
                    if (/Best Business Schools|Unranked/i.test(text)) {
                        rowText = text;
                        break;
                    }
                    if (text.length > rowText.length) {
                        rowText = text;
                    }
                }

                const displayName = (link.innerText || '').trim();
                const prev = rowsByHref.get(path);
                const prevText = prev ? prev.row_text : '';
                const prevHasExactRank = /#\d+\b/.test(prevText) && !/#\d+-\d+\b/.test(prevText);
                const currHasExactRank = /#\d+\b/.test(rowText) && !/#\d+-\d+\b/.test(rowText);

                if (
                    !prev ||
                    (currHasExactRank && !prevHasExactRank) ||
                    (currHasExactRank === prevHasExactRank && rowText.length > prevText.length)
                ) {
                    rowsByHref.set(path, {
                        href: path,
                        display_name: displayName,
                        row_text: rowText,
                    });
                }
            }

            return Array.from(rowsByHref.values());
        }
        """
    )

    print(f"  Scanning {len(extracted_rows)} links for school profiles...")

    schools = []
    for row in extracted_rows:
        row_text = row["row_text"]

        # Exclude range-ranked and unranked schools.
        if re.search(r"#\d+-\d+\b", row_text):
            continue

        rank_match = re.search(r"#(\d+)\b", row_text)
        if not rank_match:
            continue

        href = row["href"]
        if href.startswith("/"):
            url = f"https://premium.usnews.com{href}"
        elif "www.usnews.com" in href:
            url = href.replace("https://www.usnews.com", "https://premium.usnews.com")
        else:
            url = href

        slug = url.rstrip("/").split("/")[-1]
        display_name = row["display_name"] or slug.replace("-", " ").title()
        schools.append(
            {
                "name": slug,
                "url": url,
                "display_name": display_name,
            }
        )

    print(f"  [OK] Discovered {len(schools)} schools")
    if schools:
        print(f"    First: {schools[0]['display_name']}")
        print(f"    Last:  {schools[-1]['display_name']}")

    # Save to CSV for reference / resume
    csv_path = Path(SCHOOLS_CSV)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["school_name", "url", "display_name"])
        writer.writeheader()
        for s in schools:
            writer.writerow(
                {
                    "school_name": s["name"],
                    "url": s["url"],
                    "display_name": s["display_name"],
                }
            )
    print(f"  [OK] Saved school list to {csv_path}")

    return schools


# ---------------------------------------------------------------------------
# SCHOOL LIST (from CSV)
# ---------------------------------------------------------------------------


def load_schools() -> list[dict]:
    """Load school list from existing CSV (used with --skip-discover)."""
    csv_path = Path(SCHOOLS_CSV)
    if not csv_path.exists():
        print(f"  [X] {SCHOOLS_CSV} not found. Run without --skip-discover first.")
        sys.exit(1)

    schools = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            schools.append(
                {
                    "name": row["school_name"].strip(),
                    "url": row["url"].strip(),
                    "display_name": row.get("display_name", row["school_name"]).strip(),
                }
            )

    print(f"  Loaded {len(schools)} school(s) from {csv_path}")
    return schools


# ---------------------------------------------------------------------------
# SECTION EXPANSION
# ---------------------------------------------------------------------------


def _click_and_check(page, el):
    """Click an element with gradual mouse movement, then dismiss any overlay.

    Returns True if the click likely succeeded (no overlay appeared).
    """
    el.evaluate("e => e.scrollIntoView({behavior: 'smooth', block: 'center'})")
    time.sleep(random.uniform(1.0, 2.0))

    box = el.bounding_box()
    if box and box["width"] > 5 and box["height"] > 5:
        target_x = box["x"] + random.uniform(5, box["width"] - 5)
        target_y = box["y"] + random.uniform(3, box["height"] - 3)
        page.mouse.move(target_x, target_y, steps=random.randint(10, 20))
        time.sleep(random.uniform(0.1, 0.3))
        page.mouse.click(target_x, target_y)
    else:
        el.click()

    time.sleep(random.uniform(2.0, 3.5))

    # Immediately dismiss any overlay that the click may have triggered.
    # This is CRITICAL: the anti-bot overlay appears after each click,
    # and must be dismissed before the next click can succeed.
    dismiss_overlay(page)
    time.sleep(0.5)


def _count_see_less(page) -> int:
    """Count 'SEE LESS' markers on the page (= successfully expanded sections).

    Uses a broad DOM search (not limited to a/button) to catch toggle
    elements regardless of their HTML tag.
    """
    return page.evaluate("""
        () => {
            let count = 0;
            // Walk all elements; count innermost ones starting with "SEE LESS"
            for (const el of document.querySelectorAll('*')) {
                const text = (el.textContent || '').trim().toUpperCase();
                if (!text.startsWith('SEE LESS')) continue;
                if (el.offsetParent === null) continue;
                // Only count leaf-level: skip if a child also matches
                let childMatches = false;
                for (const child of el.children) {
                    if ((child.textContent || '').trim().toUpperCase().startsWith('SEE LESS')) {
                        childMatches = true;
                        break;
                    }
                }
                if (!childMatches) count++;
            }
            // Also count "LESS" (collapsed concentrations toggle)
            for (const el of document.querySelectorAll('*')) {
                const text = (el.textContent || '').trim().toUpperCase();
                if (text === 'LESS' && el.offsetParent !== null) count++;
            }
            return count;
        }
    """)


def _click_first_visible(page, text_pattern) -> bool:
    """Find the first visible element matching text_pattern, click it.

    Re-queries the DOM each time instead of iterating a stale list.
    This is critical because overlay dismissal can shift the DOM,
    making previously-collected element references stale.

    Returns True if an element was found and clicked.
    """
    try:
        locator = page.get_by_text(text_pattern)
        count = locator.count()
        for i in range(count):
            try:
                el = locator.nth(i)
                if el.is_visible():
                    _click_and_check(page, el)
                    return True
            except Exception:
                continue
    except Exception:
        pass
    return False


def expand_all_sections(page):
    """Click all expandable sections on a US News school profile page.

    There are typically 7 expandable items:
      1. SEE MORE ADMISSIONS DATA
      2. SEE MORE COST DATA
      3. SEE MORE STUDENT DATA
      4. SEE MORE SALARY DATA
      5. SEE MORE SPECIALTY DATA  (admissions)
      6. SEE MORE SPECIALTY DATA  (students)
      7. AND X MORE               (department concentrations)

    Uses page.get_by_text() to target the INNERMOST element matching
    each text pattern.  Clicks ONE element at a time, then re-queries
    the DOM for the next one.  This avoids stale element references
    after overlay dismissal shifts the DOM.
    """
    see_more_re = re.compile(r"^SEE MORE", re.IGNORECASE)
    and_more_re = re.compile(r"^AND \d+ MORE", re.IGNORECASE)
    show_all_re = re.compile(r"^Show All", re.IGNORECASE)

    total_clicked = 0

    # Click one element at a time, re-querying after each click.
    # Max 15 attempts to handle overlays causing missed clicks.
    for attempt in range(15):
        clicked = False

        # Try SEE MORE first (highest priority)
        if _click_first_visible(page, see_more_re):
            clicked = True
            total_clicked += 1
        # Then AND X MORE
        elif _click_first_visible(page, and_more_re):
            clicked = True
            total_clicked += 1
        # Then Show All
        elif _click_first_visible(page, show_all_re):
            clicked = True
            total_clicked += 1

        if not clicked:
            break

        # Check if we've expanded everything
        if _count_see_less(page) >= EXPECTED_EXPAND_SECTIONS:
            break

    print(f"  Clicked {total_clicked} element(s) in {attempt + 1} attempt(s)")

    # Final verification
    verified = _count_see_less(page)
    print(f"  Verified: {verified}/{EXPECTED_EXPAND_SECTIONS} sections expanded")

    if verified < EXPECTED_EXPAND_SECTIONS:
        print(f"  [!] Expected {EXPECTED_EXPAND_SECTIONS} but verified {verified}")

    return verified


# ---------------------------------------------------------------------------
# TARGETED TEXT EXTRACTION
# ---------------------------------------------------------------------------


def extract_metrics_text(page) -> str:
    """Extract only the school metrics region, excluding nav, ads, and footer.

    Tries the main content container first, then falls back to full body
    text with trimming.
    """
    # Try targeting a main content container (avoids header/footer by default)
    for selector in ["main", '[role="main"]', "article"]:
        try:
            el = page.locator(selector).first
            if el.is_visible():
                text = el.inner_text(timeout=10000)
                if len(text) > 500:
                    return _clean_page_text(text)
        except Exception:
            continue

    # Fallback: full body text with trimming
    text = safe_get_text(page)
    return _clean_page_text(text)


def _clean_page_text(text: str) -> str:
    """Trim page text to only the school metrics region.

    Boundaries (matching example_text.txt):
      START — "Business School Overview" paragraph
      END   — just before "Business School details based on" disclaimer

    Also removes the "Schools You Might Also Like" sponsored block.
    """
    lines = text.split("\n")

    # --- Find START ---
    start_idx = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if "Business School Overview" in stripped:
            start_idx = i
            break
        # Fallback markers
        if stripped == "At-a-Glance" or "in Best Business Schools" in stripped:
            start_idx = max(0, i - 5)
            break

    # --- Find END ---
    end_idx = len(lines)
    end_markers = [
        "Business School details based on",
        "Do you work at",
        "Reviews & Ratings",
        "MORE FROM",
        "YOU MAY ALSO LIKE",
    ]
    for i, line in enumerate(lines):
        stripped = line.strip()
        if any(stripped.startswith(m) for m in end_markers):
            end_idx = i  # Exclude this line
            break

    trimmed = lines[start_idx:end_idx]

    # --- Remove "Schools You Might Also Like" sponsored section ---
    cleaned = []
    skipping_sponsored = False
    resume_markers = {
        "Admissions",
        "Full-Time MBA Cost",
        "Student Population",
        "Academics",
        "Career & Salary",
        "Specialty Master",
    }
    for line in trimmed:
        stripped = line.strip()

        if "Schools You Might Also Like" in stripped:
            skipping_sponsored = True
            continue

        if skipping_sponsored:
            if any(stripped.startswith(m) for m in resume_markers):
                skipping_sponsored = False
            else:
                continue

        cleaned.append(line)

    # Remove stray noise lines
    cleaned = [l for l in cleaned if "SEE ALL GRAD SCHOOL RANKINGS" not in l]

    return "\n".join(cleaned)


# ---------------------------------------------------------------------------
# SCRAPE A SINGLE SCHOOL
# ---------------------------------------------------------------------------


def scrape_school(page, url: str, school_name: str) -> str | None:
    """Navigate to a school page, expand all sections, extract metrics text."""
    print(f"  Navigating to: {url}")

    if not safe_goto(page, url):
        print(f"  [X] Could not load page automatically.")
        return None

    time.sleep(4)

    # Check if redirected to login
    current_url = page.url.lower()
    if "login" in current_url or "signin" in current_url:
        print("  [!] Session expired; retrying once...")
        if not safe_goto(page, url):
            return None
        time.sleep(4)
        current_url = page.url.lower()
        if "login" in current_url or "signin" in current_url:
            print("  [X] Still redirected to login; skipping school")
            return None

    # Dismiss cookie banners / consent pop-ups
    try:
        page.evaluate("""
            () => {
                for (const txt of ['Accept', 'Accept All', 'I Accept', 'Agree', 'OK', 'Got it', 'Continue']) {
                    for (const el of document.querySelectorAll('button, a, [role="button"]')) {
                        if (el.textContent.trim() === txt && el.offsetParent !== null) {
                            el.click();
                            return;
                        }
                    }
                }
            }
        """)
    except Exception as e:
        print(f"  [!] Cookie banner dismiss skipped: {e}")
    time.sleep(0.5)

    # Strip ad iframes and ad containers from the DOM so clicks can't hit them
    strip_ad_elements(page)

    # Step 1: Scroll whole page to trigger lazy loading of all section cards
    print("  Loading all page sections...")
    scroll_full_page(page)

    # Strip again after scroll (lazy-loaded ads may have appeared)
    strip_ad_elements(page)

    # Step 2: Expand all 7 sections
    print("  Expanding sections...")
    sections_expanded = expand_all_sections(page)

    if sections_expanded == 0:
        print("  [INFO] No auto-expandable sections found.")
        print("    Continuing without manual expansion.")

    # Step 3: Scroll again to load content revealed by expansion
    scroll_full_page(page)

    # Step 4: Extract only the metrics region
    text = extract_metrics_text(page)

    if len(text.strip()) < 500:
        print(f"  [!] Very little text extracted ({len(text)} chars)")
        return None

    print(f"  [OK] Extracted {len(text):,} characters")

    # Save raw text
    PAGE_TEXTS_DIR.mkdir(parents=True, exist_ok=True)
    txt_path = PAGE_TEXTS_DIR / f"{school_name}.txt"
    txt_path.write_text(text, encoding="utf-8")
    print(f"  [OK] Saved: {txt_path}")

    return text


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------


def main():
    # Parse arguments
    force_login = "--login" in sys.argv
    scrape_only = "--scrape-only" in sys.argv
    force_discover = "--discover" in sys.argv

    if not scrape_only:
        prompt = load_prompt()
        print(f"Loaded extraction prompt ({len(prompt):,} chars)")
    else:
        prompt = None
        print("Mode: scrape-only (no API calls)")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        # Launch real Chrome/Edge with persistent profile
        print("\nLaunching browser...")
        context = launch_browser(pw)
        page = context.pages[0] if context.pages else context.new_page()

        # Login check (ad blocking is OFF so login overlay can load)
        check_and_login(page, force_login=force_login)

        # NOW enable ad blocking — login is done, we don't need
        # third-party auth domains anymore
        enable_ad_blocking(context)

        # Phase 1: Load school list from CSV, or discover from rankings table
        if force_discover or not Path(SCHOOLS_CSV).exists():
            schools = discover_schools_from_rankings(page)
        else:
            schools = load_schools()

        print(f"\n  Total schools to process: {len(schools)}")

        # Phase 2: Scrape & extract each school
        results = []
        failed = []

        for i, school in enumerate(schools, 1):
            print(f"\n{'=' * 60}")
            print(f"[{i}/{len(schools)}] {school.get('display_name', school['name'])}")
            print(f"{'=' * 60}")

            output_path = OUTPUT_DIR / f"{school['name']}.json"
            txt_path = PAGE_TEXTS_DIR / f"{school['name']}.txt"

            if output_path.exists() and not scrape_only:
                print(f"  [SKIP] Already extracted; skipping")
                continue

            if scrape_only and txt_path.exists():
                print(f"  [SKIP] Already scraped; skipping")
                continue

            # Scrape the page
            page_text = scrape_school(page, school["url"], school["name"])
            if not page_text:
                failed.append(school["name"])
                continue

            if scrape_only:
                results.append({"name": school["name"]})
                continue

            # Extract via Claude Sonnet 4 API
            print("  Sending to Claude Sonnet 4 API...")
            start = time.time()
            data = extract_school_data(
                page_text=page_text,
                prompt_text=prompt,
                source_url=school["url"],
            )
            elapsed = time.time() - start
            print(f"  API time: {elapsed:.1f}s")

            if "_error" in data:
                print(f"  [!] Extraction error: {data['_error']}")
                failed.append(school["name"])
            elif "school_info" in data:
                info = data["school_info"]
                print(
                    f"  School: {info.get('school_name', '?')} ({info.get('business_school_name', '?')})"
                )
                print(f"  Rank: #{info.get('us_news_rank', '?')}")

            save_json(data, output_path)
            results.append(data)

            # Delay between schools
            if i < len(schools):
                print(f"  Waiting {DELAY_BETWEEN_PAGES}s...")
                time.sleep(DELAY_BETWEEN_PAGES)

        context.close()

    # Summary
    print(f"\n{'=' * 60}")
    print("DONE")
    print(f"{'=' * 60}")
    print(f"  [OK] Processed: {len(results)} school(s)")
    if failed:
        print(f"  [X] Failed:    {len(failed)}: {', '.join(failed)}")
    print(f"  JSON:  {OUTPUT_DIR.resolve()}")
    print(f"  Texts: {PAGE_TEXTS_DIR.resolve()}")

    if not scrape_only:
        print(f"\nRun 'python combine_results.py' to merge into Excel/CSV")

    if scrape_only:
        print(
            f"\nText files saved. Run 'python extract_batch.py' to extract JSON from them."
        )


if __name__ == "__main__":
    main()
