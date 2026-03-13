import scraper
from bs4 import BeautifulSoup

html = scraper.get_html('https://timetables.jreast.co.jp/2602/train/065/066661.html')
soup = BeautifulSoup(html, 'html.parser')

print("=== 列車名 ===")
title = soup.find('h1', class_='train_name')
if title: print(title.get_text().strip())

print("\n=== 日付・運行情報 ===")
date = soup.find('div', class_='train_date')
if date: print(date.get_text().strip())

print("\n=== テーブル行 ===")
for tr in soup.find_all('tr'):
    cells = [td.get_text().strip() for td in tr.find_all(['th', 'td'])]
    if cells:
        print(" | ".join(cells))
