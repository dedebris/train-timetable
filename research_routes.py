import scraper

stations = {
    "東京": "1039",
    "上野": "0204",
    "品川": "0788",
    "大宮": "0350",
    "新宿": "0866"
}

for name, sid in stations.items():
    url = f"https://timetables.jreast.co.jp/2603/list/list{sid}.html"
    print(f"\n--- {name} ({url}) ---")
    routes = scraper.parse_station_list(url)
    for r in routes:
        # 簡易フィルタ: 特急や新幹線に関係がありそうな名前か、上り・着などのキーワード
        is_relevant = any(k in r['route_name'] for k in ["新幹線", "特急", "エクスプレス", "上り", "南行"])
        if is_relevant:
            print(f"{r['route_name']} ({r['day_type']}): {r['url']}")
