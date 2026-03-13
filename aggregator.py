import scraper
from datetime import datetime
import json
import logging
import urllib.parse
import re

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def in_time_range(t_str, start_time, end_time, cross_midnight=False):
    if not t_str or "歩" in t_str or "??Resource" in t_str or "??:" in t_str:
        return False
        
    m = re.match(r'^(\d{1,2}):(\d{2})$', t_str.strip())
    if not m:
        return False
        
    try:
        t_val = datetime.strptime(t_str, "%H:%M").time()
        s_val = datetime.strptime(start_time, "%H:%M").time()
        e_val = datetime.strptime(end_time, "%H:%M").time()
        
        if cross_midnight:
            return True
            
        if s_val <= e_val:
            return s_val <= t_val <= e_val
        else:
            return s_val <= t_val or t_val <= e_val
    except Exception as e:
        return False

def check_operation_date(date_str, target_date_iso, operating_days_list=None):
    if operating_days_list is not None:
        if not operating_days_list:
            if date_str and "毎日運転" in date_str:
                return True
        return target_date_iso in operating_days_list

    if not date_str or date_str.strip() == "":
        return True
    if "毎日運転" in date_str:
        return True
    if "運休" in date_str:
        dt = datetime.strptime(target_date_iso, "%Y-%m-%d")
        weekday = dt.weekday()
        if "土曜・休日" in date_str and weekday >= 5:
            return False
    return True

def str_to_bool_str(is_op):
    return "◯" if is_op else "X"

def extract_trains_for_station(station_url, start_time, end_time, target_date_str, 
                                day_type_filter, target_station_name, 
                                exclude_routes=[], cross_midnight=False):
    
    routes = scraper.parse_station_list(station_url)
    
    if exclude_routes:
        routes = [r for r in routes if not any(ex in r['route_name'] for ex in exclude_routes)]
        
    target_routes = [r for r in routes if r['day_type'] == day_type_filter]
    
    results = []
    
    for r in target_routes:
        is_shinkansen_or_tokkyu = "新幹線" in r['route_name'] or "エクスプレス" in r['route_name'] or "特急" in r['route_name']
        
        logging.info(f"Processing route: {r['route_name']}")
        trains = scraper.parse_timetable(r['url'])
        
        for t in trains:
            if not in_time_range(t['time'], start_time, end_time, cross_midnight):
                continue
                
            is_shinkansen_or_tokkyu_train = is_shinkansen_or_tokkyu or t.get('is_limited_express')
            
            if is_shinkansen_or_tokkyu_train:
                info = scraper.parse_train_info(t['url'], target_station_name)
                if info:
                    disp_time = t['time']
                    pf = info["platform"]
                    arr_dep = "発"
                    
                    if info.get("arrival_time") and not info.get("departure_time") and target_station_name == "東京":
                        disp_time = info.get("arrival_time")
                        arr_dep = "着"

                    m_date = re.search(r'(\d+)/(\d+)', target_date_str)
                    target_date_iso = f"2026-{m_date.group(1).zfill(2)}-{m_date.group(2).zfill(2)}" if m_date else "2026-01-01"

                    results.append({
                        "route": r['route_name'],
                        "route_url": r['url'],
                        "train_name": info['train_name'],
                        "train_number": info.get("train_number", ""),
                        "equipment": info.get("equipment", ""),
                        "train_model": info.get("train_model", ""),
                        "section": info.get("section", ""),
                        "platform": pf,
                        "operation": str_to_bool_str(check_operation_date(info["operation_dates"], target_date_iso, info.get("operating_days_list"))),
                        "url": t['url'],
                        "arrival_time": info.get("arrival_time"),
                        "departure_time": info.get("departure_time"),
                        "time": t['time'],
                        "target_date": target_date_str,
                        "is_diamond": t['has_diamond'],
                        "is_origin": info.get("is_origin", False),
                        "is_destination": info.get("is_destination", False),
                        "is_local": False
                    })
            else:
                static_pf_map = {
                    "東京": {
                        "中央線快速": "1・2番線",
                        "山手線": "4・5番線",
                        "京浜東北線・根岸線": "3・6番線",
                        "東海道線(上野東京ライン)": "9・10番線",
                        "上野東京ライン(宇都宮線・高崎線)": "7・8番線",
                        "上野東京ライン(常磐線)": "7・8番線",
                        "総武線快速": "総武地下1-4番線",
                        "横須賀線": "総武地下1-4番線",
                        "京葉線・武蔵野線": "京葉地下1-4番線"
                    },
                    "盛岡": {
                        "東北本線": "5-7番線",
                        "山田線": "4・6番線",
                        "田沢湖線": "8・9番線",
                        "ＩＧＲいわて銀河鉄道線": "0・1番線"
                    }
                }
                
                raw_name = r.get('raw_route_name', r['route_name'])
                existing = None
                for res in results:
                    if res.get('is_noriba') and res.get('raw_route_name') == raw_name:
                        existing = res
                        break
                
                if not existing:
                    info = scraper.parse_train_info(t['url'], target_station_name)
                    pf_scraped = info["platform"] if info else t.get('platform', '')
                    pf_static = static_pf_map.get(target_station_name, {}).get(raw_name)
                    pf = pf_static if pf_static else pf_scraped
                    
                    existing = {
                        "route": raw_name,
                        "raw_route_name": raw_name,
                        "platform": pf,
                        "target_date": target_date_str,
                        "is_local": True,
                        "is_noriba": True,
                        "links": []
                    }
                    results.append(existing)
                
                link_item = {"name": r['route_name'], "url": r['url']}
                if link_item not in existing["links"]:
                    existing["links"].append(link_item)
                
    return results

def extract_req1():
    logging.info("Start Req1")
    dep = extract_trains_for_station(
        "https://timetables.jreast.co.jp/2603/list/list1039.html",
        "14:00", "17:00", "3/29(日)", "土曜・休日", "東京",
        exclude_routes=["東海道・山陽新幹線"]
    )
    
    monitor_urls = [
        "https://timetables.jreast.co.jp/2603/list/list0350.html",
        "https://timetables.jreast.co.jp/2603/list/list0204.html",
        "https://timetables.jreast.co.jp/2603/list/list0788.html",
        "https://timetables.jreast.co.jp/2603/list/list0866.html",
        "https://timetables.jreast.co.jp/2603/list/list0340.html"
    ]
    
    arr_collected = []
    for m_url in monitor_urls:
        res = extract_trains_for_station(
            m_url, "13:00", "17:00", "3/29(日)", "土曜・休日", "東京"
        )
        arr_collected.extend(res)
    
    arr_filtered = []
    for a in arr_collected:
        if a.get('is_local'): continue
        # 東海道・山陽新幹線（上り）を除外
        if "東海道・山陽新幹線" in a.get('route', ''):
            continue
        arr_time = a.get('arrival_time')
        if arr_time and in_time_range(arr_time, "14:00", "17:00"):
            a['arr_dep'] = "着"
            a['time'] = arr_time
            arr_filtered.append(a)
    
    return dep + arr_filtered

def extract_req2():
    logging.info("Start Req2")
    r_sun = extract_trains_for_station(
        "https://timetables.jreast.co.jp/2603/list/list0350.html",
        "15:00", "23:59", "3/29(日)", "土曜・休日", "大宮"
    )
    r_mon = extract_trains_for_station(
        "https://timetables.jreast.co.jp/2603/list/list0350.html",
        "00:00", "23:59", "3/30(月)", "平日", "大宮", cross_midnight=True
    )
    r_tue = extract_trains_for_station(
        "https://timetables.jreast.co.jp/2603/list/list0350.html",
        "00:00", "15:00", "3/31(火)", "平日", "大宮"
    )
    return r_sun + r_mon + r_tue

def extract_req3():
    logging.info("Start Req3")
    r_tue = extract_trains_for_station(
        "https://timetables.jreast.co.jp/2603/list/list1565.html",
        "14:00", "23:59", "3/31(火)", "平日", "盛岡"
    )
    r_wed = extract_trains_for_station(
        "https://timetables.jreast.co.jp/2603/list/list1565.html",
        "00:00", "14:00", "4/1(水)", "平日", "盛岡"
    )
    return r_tue + r_wed

def extract_req4():
    logging.info("Start Req4")
    dep = extract_trains_for_station(
        "https://timetables.jreast.co.jp/2603/list/list1039.html",
        "13:00", "16:00", "4/1(水)", "平日", "東京",
        exclude_routes=["東海道・山陽新幹線"]
    )
    
    monitor_urls = [
        "https://timetables.jreast.co.jp/2603/list/list0350.html",
        "https://timetables.jreast.co.jp/2603/list/list0204.html",
        "https://timetables.jreast.co.jp/2603/list/list0788.html",
        "https://timetables.jreast.co.jp/2603/list/list0866.html",
        "https://timetables.jreast.co.jp/2603/list/list0340.html"
    ]
    
    arr_collected = []
    for m_url in monitor_urls:
        res = extract_trains_for_station(
            m_url, "12:00", "16:00", "4/1(水)", "平日", "東京"
        )
        arr_collected.extend(res)
    
    arr_filtered = []
    for a in arr_collected:
        if a.get('is_local'): continue
        if "東海道・山陽新幹線" in a.get('route', ''):
            continue
        arr_time = a.get('arrival_time')
        if arr_time and in_time_range(arr_time, "13:00", "16:00"):
            a['arr_dep'] = "着"
            a['time'] = arr_time
            arr_filtered.append(a)
            
    return dep + arr_filtered

def remove_duplicates(train_list):
    if not train_list:
        return []
    
    # URLと時刻をキーにして集約
    groups = {}
    
    noriba_groups = {}
    for t in train_list:
        if t.get('is_noriba'):
            key = (t['route'], t['platform'])
            if key not in noriba_groups:
                noriba_groups[key] = t.copy()
    
    for t in train_list:
        if t.get('is_local'): continue
            
        url = t.get('url', '')
        if not url or url == '#':
            url = f"dummy_{id(t)}"
            
        key = (url, t.get('target_date'), t.get('arrival_time'), t.get('departure_time'))
        
        if key not in groups:
            t_copy = t.copy()
            t_copy['route_links'] = [{"name": t.get('route', ''), "url": t.get('route_url', '')}]
            groups[key] = t_copy
        else:
            existing = groups[key]
            if 'route_links' not in existing:
                existing['route_links'] = [{"name": existing.get('route', ''), "url": existing.get('route_url', '')}]
            
            new_route_name = t.get('route', '')
            new_route_url = t.get('route_url', '')
            if not any(link['name'] == new_route_name for link in existing['route_links']):
                existing['route_links'].append({"name": new_route_name, "url": new_route_url})

            r1 = existing.get('route', '')
            if new_route_name and new_route_name not in r1:
                existing['route'] = f"{r1}・{new_route_name}"
                
            n1 = existing.get('train_name', '')
            n2 = t.get('train_name', '')
            
            def get_names_and_type(full_name):
                is_split = " 分割" in full_name
                base = full_name.replace(" 併結", "").replace(" 分割", "")
                return [n.strip() for n in base.split('・') if n.strip()], is_split
            
            names1, split1 = get_names_and_type(n1)
            names2, split2 = get_names_and_type(n2)
            
            for new_n in names2:
                if new_n not in names1:
                    names1.append(new_n)
            
            new_train_name = '・'.join(names1)
            if len(names1) >= 2:
                new_train_name += " 分割" if (split1 or split2) else " 併結"
            existing['train_name'] = new_train_name
            
            s1 = existing.get('section', '')
            s2 = t.get('section', '')
            secs1 = [s.strip() for s in s1.split('、') if s.strip()]
            secs2 = [s.strip() for s in s2.split('、') if s.strip()]
            for new_s in secs2:
                if new_s not in secs1:
                    secs1.append(new_s)
            existing['section'] = '、'.join(secs1)
                  
    aggregated = list(groups.values())
    noriba_list = list(noriba_groups.values())
    
    def sort_key(t):
        if t.get('is_noriba'):
            return ("ZZZ_NORIBA", t.get('platform', ''))
        d = t.get('target_date', '')
        ti = t.get('arrival_time') or t.get('departure_time') or t.get('time', '99:99')
        return (d, ti)
        
    return sorted(aggregated + noriba_list, key=sort_key)

def run_all():
    all_data = {
        "req1": remove_duplicates(extract_req1()),
        "req2": remove_duplicates(extract_req2()),
        "req3": remove_duplicates(extract_req3()),
        "req4": remove_duplicates(extract_req4()),
    }
    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    logging.info("Finished Scraping. Results saved to results.json")

if __name__ == "__main__":
    run_all()
