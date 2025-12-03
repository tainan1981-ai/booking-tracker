import json
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
import gspread
from google.oauth2.service_account import Credentials

# ================================
# Google Sheets 設定
# ================================
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def init_gsheet():
    service_info = json.loads(open("service_account.json").read())
    creds = Credentials.from_service_account_info(service_info, scopes=SCOPES)
    gc = gspread.authorize(creds)
    ss_id = open("spreadsheet_id").read().strip()
    sheet = gc.open_by_key(ss_id).sheet1
    return sheet

# ================================
# Booking URL 設定（兩區）
# ================================
AREAS = {
    "台南市": "https://www.booking.com/searchresults.zh-tw.html?ss=台南市&checkin={}&checkout={}",
    "台南中西區": "https://www.booking.com/searchresults.zh-tw.html?ss=台南+中西區&checkin={}&checkout={}",
}

# ================================
# Playwright 爬蟲（雲端友善版本）
# ================================
async def fetch_booking_rooms(area_name, url):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            await page.goto(url, timeout=60000)

            # 等待搜尋結果
            await page.wait_for_selector("div[data-testid='property-card']", timeout=60000)

            hotels = await page.query_selector_all("div[data-testid='property-card']")
            count = len(hotels)

            await browser.close()
            return count

    except Exception as e:
        print(f"❌ {area_name} 抓取失敗：{e}")
        return "error"


# ================================
# Main 主程式
# ================================
async def main():
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now().replace(day=datetime.now().day + 1)).strftime("%Y-%m-%d")

    sheet = init_gsheet()

    results = []
    print("🚀 開始雲端 Booking 爬蟲...")

    for name, link in AREAS.items():
        url = link.format(today, tomorrow)
        print(f"➡️ 抓取 {name} ...")

        rooms = await fetch_booking_rooms(name, url)
        results.append(rooms)

    new_row = [today] + results
    sheet.append_row(new_row)

    print("✅ 寫入 Google Sheets 完成！")
    print(new_row)


if __name__ == "__main__":
    asyncio.run(main())
