import scraper
import json

# テスト用のURL (やまびこ 63号: グランクラスあり)
url = 'https://timetables.jreast.co.jp/2603/train/060/062261.html'
info = scraper.parse_train_info(url, '東京')

if info:
    print(f"Train Name: {info['train_name']}")
    print(f"Train Number: {info['train_number']}")
    print(f"Equipment: {info['equipment']}")
    print(f"Model: {info['train_model']}")
else:
    print("Failed to parse train info.")
