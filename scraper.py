import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import os
import hashlib
import time
import re
import unicodedata

CACHE_DIR = "cache"
BASE_URL = "https://timetables.jreast.co.jp/"

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def estimate_train_model(train_name, train_number, components, equipment):
    """
    列車名、列車番号、設備情報から車両形式を推定する。
    """
    # 正規化して判定精度を高める
    norm_name = unicodedata.normalize('NFKC', train_name).replace('・', '-')
    names = norm_name.split('-')
    models = []
    
    for name in names:
        model = "不明"
        
        # 特急・新幹線の車両形式判定
        if "草津" in name or "四万" in name or "あかぎ" in name:
            model = "E257系"
        elif "きぬがわ" in name:
            model = "253系"
        elif "日光" in name: # スペーシア日光
            model = "東武100系"
        elif "ひたち" in name or "ときわ" in name:
            model = "E657系"
        elif "成田エクスプレス" in name:
            model = "E259系"
        elif "あずさ" in name or "かいじ" in name or "富士回遊" in name:
            model = "E353系"
        elif "わかしお" in name or "さざなみ" in name or "しおさい" in name or "踊り子" in name or "湘南" in name:
            model = "E257系"
        elif "サフィール" in name:
            model = "E261系"
        elif "はやぶさ" in name or "はやて" in name:
            h5_candidates = ["10号", "22号", "28号", "95号", "17号", "21号", "29号", "39号", "42号"]
            if any(cand in name for cand in h5_candidates):
                model = "E5系/H5系"
            else:
                model = "E5系"
        elif "こまち" in name:
            model = "E6系"
        elif "やまびこ" in name or "なすの" in name:
            if "223号" in name or "グランクラス" in equipment:
                model = "E5系"
            else:
                model = "E2系"
        elif "つばさ" in name:
            e8_numbers = ["121号", "122号", "124号", "127号", "129号", "131号", "133号", 
                          "138号", "140号", "141号", "142号", "143号", "145号", "146号", 
                          "150号", "153号", "157号", "158号", "160号"]
            if "グランクラス" in equipment or any(num in name for num in e8_numbers):
                model = "E8系"
            else:
                model = "E3系/E8系"
        elif "とき" in name or "たにがわ" in name:
            if "グランクラス" in equipment:
                model = "E7系"
            else:
                model = "E2系/E7系"
        elif any(n in name for n in ["かがやき", "はくたか", "あさま", "つるぎ"]):
            model = "E7系/W7系"
            
        if model not in models:
            models.append(model)
    return "・".join(models)

def get_html(url, use_cache=True):
    url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
    cache_path = os.path.join(CACHE_DIR, f"{url_hash}.html")
    if use_cache and os.path.exists(cache_path):
        with open(cache_path, 'r', encoding='utf-8') as f:
            return f.read()
    print(f"Fetching: {url}")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        html = urllib.request.urlopen(req).read().decode('utf-8')
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(html)
        time.sleep(1)
        return html
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_station_list(station_url):
    html = get_html(station_url)
    if not html:
        return []
    soup = BeautifulSoup(html, 'html.parser')
    routes = []
    for a in soup.find_all('a', class_='fortimeLink'):
        href = a.get('href')
        day_type = a.get_text().strip()
        if href and '../timetable/tt' in href:
            full_url = urllib.parse.urljoin(station_url, href)
            parent_td = a.find_parent('td')
            if parent_td:
                th = parent_td.find_previous_sibling('th')
                if th:
                    raw_name = th.get_text().strip()
                    direction_text = ""
                    tds = th.find_parent('tr').find_all('td')
                    if tds:
                        direction_text = tds[0].get_text().strip()
                    direction = ""
                    if "(下り)" in direction_text: direction = "（下り）"
                    elif "(上り)" in direction_text: direction = "（上り）"
                    elif "(外回り)" in direction_text: direction = "（外回り）"
                    elif "(内回り)" in direction_text: direction = "（内回り）"
                    elif "(南行)" in direction_text: direction = "（南行）"
                    elif "(北行)" in direction_text: direction = "（北行）"
                    if not direction:
                        if href.endswith('0.html'): direction = "（下り）"
                        elif href.endswith('1.html'): direction = "（上り）"
                    routes.append({
                        "route_name": f"{raw_name}{direction}",
                        "raw_route_name": raw_name,
                        "direction": direction,
                        "day_type": day_type,
                        "url": full_url
                    })
    return routes

def parse_train_info(train_url, target_station):
    html = get_html(train_url)
    if not html:
        return None
    soup = BeautifulSoup(html, 'html.parser')
    info = {
        "url": train_url, "train_type": "", "train_name": "", "train_number": "",
        "equipment": "", "train_model": "", "operation_dates": "",
        "arrival_time": "", "departure_time": "", "platform": "", "section": ""
    }
    col_stations = []
    coupling_info = []
    for tr in soup.find_all('tr'):
        th_val = tr.find('th')
        td_vals = tr.find_all('td')
        if th_val and td_vals:
            th_text = th_val.get_text().strip()
            td_texts = [td.get_text().strip() for td in td_vals]
            if not col_stations:
                if th_text == "列車名":
                    col_stations = [[] for _ in range(len(td_texts))]
            if th_text == "列車種別":
                unique_types = []
                for t in td_texts:
                    if t and t not in unique_types: unique_types.append(t)
                info["train_type"] = "・".join(unique_types)
            elif th_text == "列車名":
                train_names = [t for t in td_texts if t]
                info["train_name"] = "・".join(train_names)
            elif th_text == "列車番号":
                info["train_number"] = "・".join([t for t in td_texts if t])
            elif th_text == "設備":
                eq_list = []
                for td in td_vals:
                    items = td.find_all('li')
                    if items: eq_list.extend([li.get_text().strip() for li in items])
                    else:
                        text = td.get_text().strip()
                        if text: eq_list.append(text)
                info["equipment"] = "、".join(eq_list)
            elif th_text == "運転日":
                info["operation_dates"] = td_texts[0] if td_texts else ""
            elif th_text == "併結運転":
                coupling_info = td_texts

        cells = tr.find_all(['th', 'td'])
        if len(cells) >= 2:
            st_name = cells[0].get_text().strip()
            if st_name == "駅名": continue
            for i in range(len(col_stations)):
                idx = 1 + i * 2
                if idx < len(cells):
                    time_val = cells[idx].get_text().strip()
                    is_time = re.search(r'\d{2}:\d{2}', time_val) or any(s in time_val for s in ["発", "着", "レ", "||", "--"])
                    if is_time: col_stations[i].append(st_name)
            if st_name == target_station:
                time_cell = cells[1]
                time_text = time_cell.get_text().strip()
                if "着" in time_text:
                    arr_matches = re.findall(r'(\d{2}:\d{2})\s*着', time_text)
                    if arr_matches: info["arrival_time"] = arr_matches[0]
                if "発" in time_text:
                    dep_matches = re.findall(r'(\d{2}:\d{2})\s*発', time_text)
                    if dep_matches: info["departure_time"] = dep_matches[0]
                
                cell_html = str(time_cell)
                if "分割" in cell_html: info["is_split"] = True
                elif "併結" in cell_html: info["is_split"] = False

                # 始発・終着判定
                # 1. テキストによる明示的な判定
                if "当駅始発" in time_text or "始発" in time_text:
                    info["is_origin"] = True
                if "当駅止まり" in time_text or "止まり" in time_text:
                    info["is_destination"] = True
                
                # 2. 時刻の有無による判定 (補完)
                # 到着時刻がなく出発時刻のみがある場合は始発
                if not info.get("arrival_time") and info.get("departure_time"):
                    info["is_origin"] = True
                # 到着時刻があり出発時刻がない場合は終着
                if info.get("arrival_time") and not info.get("departure_time"):
                    info["is_destination"] = True

                if len(cells) >= 3:
                    info["platform"] = cells[2].get_text().strip()

    info["operating_days_list"] = []
    cal_div = soup.find('div', class_='serviceDayCalendar')
    if cal_div:
        for table in cal_div.find_all('table', class_='calendar-month'):
            caption = table.find('caption')
            if caption:
                month_text = caption.get_text().strip()
                m = re.search(r'(\d+)年(\d+)月', month_text)
                if m:
                    year = m.group(1)
                    month = m.group(2).zfill(2)
                    for td in table.find_all('td', class_='ok'):
                        day_text = td.get_text().strip()
                        if day_text.isdigit():
                            day = day_text.zfill(2)
                            info["operating_days_list"].append(f"{year}-{month}-{day}")

    if not info["arrival_time"] and not info["departure_time"]:
        return None

    if "is_split" not in info:
        info["is_split"] = "分割" in soup.get_text()

    title_train_names = []
    title_sections = []
    for target in soup.find_all(['div', 'p', 'th', 'td']):
        if target.find(['div', 'p']): continue
        text = target.get_text().strip()
        m = re.search(r'(.+?)（([^（）]+－[^（）]+)）', text)
        if m:
            t_name = m.group(1).strip()
            t_name = re.sub(r'^.*?時刻表\s+停車駅一覧（', '', t_name).replace("新幹線", "").strip()
            s_full = m.group(2).strip()
            if t_name and t_name not in title_train_names: title_train_names.append(t_name)
            if s_full and s_full not in title_sections: title_sections.append(s_full)

    if title_train_names:
        if len(title_train_names) >= 2:
            if info.get("is_split") and target_station == "盛岡":
                suffix = " 分割"
            else:
                suffix = " 併結"
            info["train_name"] = "・".join(title_train_names) + suffix
        else:
            info["train_name"] = title_train_names[0]
        info["section"] = "、".join(title_sections)
    else:
        sections = []
        train_names_list = info["train_name"].split("・")
        for i, st_list in enumerate(col_stations):
            if st_list:
                start_st, end_st = st_list[0], st_list[-1]
                if i > 0 and col_stations[0]:
                    if coupling_info and i < len(coupling_info):
                        m = re.search(r'([^－]+)－[^は]+は', coupling_info[i])
                        if m: start_st = m.group(1)
                sec_text = f"{start_st}－{end_st}"
                if len(col_stations) > 1 and i < len(train_names_list):
                    sections.append(f"{sec_text}（{train_names_list[i]}）")
                else: sections.append(sec_text)
            else: sections.append("不明")
        info["section"] = "・".join(sections)
    
    info["train_model"] = estimate_train_model(info["train_name"], info["train_number"], [], info["equipment"])
    return info

def parse_timetable(timetable_url):
    html = get_html(timetable_url)
    if not html: return []
    soup = BeautifulSoup(html, 'html.parser')
    limited_express_symbols = set(["はぶ", "こ", "や", "つ", "と", "あ", "か", "はく", "な", "つる"])
    legend_section = soup.find('dt', string=re.compile(r'列車種別・列車名'))
    if legend_section:
        dd = legend_section.find_next_sibling('dd')
        if dd:
            text = dd.get_text().strip()
            pairs = re.findall(r'([^=＝\s]+)[=＝]([^=＝\s]+)', text)
            for symbol, name in pairs:
                if '特急' in name or any(n in name for n in ["はやぶさ", "こまち", "やまびこ", "つばさ", "とき", "あさま", "かがやき", "はくたか", "なすの", "つるぎ"]):
                    limited_express_symbols.add(symbol)
    trains = []
    for div in soup.find_all('div', class_='timetable_time'):
        data_train = div.get('data-train', '')
        symbols = data_train.split(',')
        is_limited_express = any(s in limited_express_symbols for s in symbols)
        if not is_limited_express:
            if div.find('span', class_='txt_red'): is_limited_express = True
        a = div.find('a')
        if not a: continue
        href = a.get('href')
        if href and '../../train/' in href:
            full_url = urllib.parse.urljoin(timetable_url, href)
            time_text = a.get_text().strip()
            has_diamond = "◆" in time_text
            minute_match = re.search(r'(\d+)', time_text)
            minute = minute_match.group(1).zfill(2) if minute_match else "00"
            parent_tr = div.find_parent('tr')
            hour, platform = "", ""
            if parent_tr:
                th_or_td = parent_tr.find(['th', 'td'])
                if th_or_td:
                    text = th_or_td.get_text().strip()
                    hour_match = re.search(r'(\d+)時', text)
                    if hour_match: hour = hour_match.group(1).zfill(2)
                    elif text.isdigit(): hour = text.zfill(2)
                tds = parent_tr.find_all(['td', 'th'])
                if len(tds) >= 4:
                    for cell in reversed(tds):
                        c_text = cell.get_text().strip()
                        if not c_text: continue
                        if "番線" in c_text:
                            m = re.search(r'(\d+番線)', c_text)
                            if m:
                                platform = m.group(1)
                                break
                        if c_text.isdigit() and len(c_text) <= 2:
                            if cell != tds[0]:
                                platform = c_text + "番線"
                                break
            trains.append({
                "time": f"{hour}:{minute}" if hour else f"??:{minute}",
                "has_diamond": has_diamond, "url": full_url,
                "is_limited_express": is_limited_express, "platform": platform
            })
    return trains
