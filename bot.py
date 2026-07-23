import asyncio
import os
import logging
import json
from urllib.parse import urlparse
import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Fetch environment variables
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CAPSOLVER_API_KEY = os.environ.get("CAPSOLVER_API_KEY")  # Optional: For hard CAPTCHA solving

def is_valid_url(url):
    """Basic URL validation."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

async def solve_recaptcha_v2(site_url: str, site_key: str) -> str:
    """
    Solves reCAPTCHA v2 using CapSolver API asynchronously.
    Returns the g-recaptcha-response token or None.
    """
    if not CAPSOLVER_API_KEY:
        logger.warning("CapSolver API key not provided in environment variables.")
        return None

    async with aiohttp.ClientSession() as session:
        # Create task
        create_task_payload = {
            "clientKey": CAPSOLVER_API_KEY,
            "task": {
                "type": "ReCaptchaV2TaskProxyLess",
                "websiteURL": site_url,
                "websiteKey": site_key
            }
        }
        
        async with session.post("https://api.capsolver.com/createTask", json=create_task_payload) as resp:
            data = await resp.json()
            if data.get("errorId", 0) != 0:
                logger.error(f"CapSolver createTask error: {data.get('errorDescription')}")
                return None
            task_id = data.get("taskId")

        # Poll for result
        for _ in range(30):  # Wait up to 60s
            await asyncio.sleep(2)
            get_result_payload = {
                "clientKey": CAPSOLVER_API_KEY,
                "taskId": task_id
            }
            async with session.post("https://api.capsolver.com/getTaskResult", json=get_result_payload) as resp:
                res_data = await resp.json()
                status = res_data.get("status")
                if status == "ready":
                    return res_data.get("solution", {}).get("gRecaptchaResponse")
                elif status == "failed":
                    logger.error("CapSolver task failed.")
                    return None
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message when the command /start is issued."""
    welcome_text = (
        "🤖 *Welcome to the Stealth Web Automation Bot!*\n\n"
        "Send me a link using `/check <URL>` and I'll spin up an anti-detect browser environment.\n\n"
        "*Commands available:*\n"
        "• `/check <url>` — Stealth browse, handle CAPTCHAs, and return screenshot."
    )
    await update.message.reply_markdown(welcome_text)

async def check_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /check command with stealth flags and optional CAPTCHA handling."""
    chat_id = update.effective_chat.id
    
    if not context.args:
        await update.message.reply_text("⚠️ Please provide a URL. Example: /check https://example.com")
        return

    url = context.args[0]
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    if not is_valid_url(url):
        await update.message.reply_text("⚠️ Invalid URL provided. Please include http:// or https://")
        return

    status_message = await update.message.reply_text(f"⏳ Launching stealth browser for {url}...")
    screenshot_path = f"screenshot_{chat_id}.png"
    
    try:
        async with async_playwright() as p:
            # Launch Chromium with anti-detection args
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-infobars",
                    "--window-position=0,0",
                    "--ignore-certificate-errors"
                ]
            )
            
            # Create a realistic context masking automation signals
            browser_context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 800},
                device_scale_factor=1,
                has_touch=False,
                is_mobile=False,
                locale="en-US",
                timezone_id="America/New_York"
            )
            
            page = await browser_context.new_page()

            # Inject script to override navigator.webdriver and common bot indicators
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            """)
            
            await status_message.edit_text(f"🌐 Navigating to {url}...")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Give dynamic JS or Cloudflare Turnstile a few seconds to evaluate
            await page.wait_for_timeout(3000)

            # Check for reCAPTCHA v2 iframe on page
            captcha_frame = page.locator('iframe[src*="recaptcha/api2/anchor"]')
            if await captcha_frame.count() > 0:
                await status_message.edit_text("🧩 CAPTCHA detected! Attempting automated solve...")
                
                # Extract sitekey
                sitekey_element = page.locator('.g-recaptcha, [data-sitekey]')
                sitekey = None
                if await sitekey_element.count() > 0:
                    sitekey = await sitekey_element.first.get_attribute("data-sitekey")

                if sitekey and CAPSOLVER_API_KEY:
                    token = await solve_recaptcha_v2(page.url, sitekey)
                    if token:
                        await status_message.edit_text("✅ CAPTCHA solved! Injecting response token...")
                        await page.evaluate(f'document.getElementById("g-recaptcha-response").value="{token}";')
                        # Attempt to click submit or trigger callback if present
                        await page.evaluate('if(typeof recaptchaCallback === "function") { recaptchaCallback(); }')
                        await page.wait_for_timeout(2000)
                    else:
                        await status_message.edit_text("⚠️ CAPTCHA solver failed or timed out. Proceeding anyway...")
                else:
                    await status_message.edit_text("⚠️ CAPTCHA detected but CAPSOLVER_API_KEY is not set. Proceeding...")

            # Smooth scroll down to trigger lazy loading
            await page.mouse.wheel(delta_x=0, delta_y=800)
            await page.wait_for_timeout(1000)
            
            page_title = await page.title()
            
            await status_message.edit_text("📸 Capturing screenshot...")
            await page.screenshot(path=screenshot_path, full_page=True)
            
            await browser.close()

        await status_message.edit_text("✅ Task completed! Uploading screenshot...")
        
        caption = f"📄 *Title:* {page_title}\n🔗 *URL:* {url}"
        
        with open(screenshot_path, 'rb') as photo:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=caption,
                parse_mode='Markdown'
            )
            
        await status_message.delete()
        os.remove(screenshot_path)

    except PlaywrightTimeoutError:
        await status_message.edit_text("❌ Timed out loading page. The site may be blocking automated headless requests.")
    except Exception as e:
        logger.error(f"Error checking URL: {e}")
        await status_message.edit_text(f"❌ Error: {str(e)}")
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)

def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set.")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("check", check_url))

    logger.info("Stealth Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

