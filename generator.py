import json
import os
import re
import unicodedata

def get_train_info_url(model, name):
    base_url = "https://www.jreast.co.jp/train/"
    # 特急 (具体的な名称・形式から先にチェック)
    # 草津・四万・あかぎ
    if any(x in name for x in ["草津・四万", "あかぎ"]): return base_url + "express/akagi.html"
    # きぬがわ
    if "きぬがわ" in name: return base_url + "express/kinugawa.html"
    # スペーシア日光
    if "スペーシア日光" in name: return "https://www.tobu.co.jp/railway/special_express/vehicle/spacia/"

    # サフィール踊り子
    if "E261" in model or "サフィール" in name: return "https://www.jreast.co.jp/saphir/"
    # 成田エクスプレス
    if "E259" in model or "成田エクスプレス" in name: return base_url + "express/nex.html"
    # ひたち・ときわ
    if "E657" in model or any(x in name for x in ["ひたち", "ときわ"]): return base_url + "express/hitachi_tokiwa.html"
    # あずさ・かいじ
    if "E353" in model or any(x in name for x in ["あずさ", "かいじ", "富士回遊"]): return base_url + "express/azusa_kaiji.html"
    # わかしお・さざなみ・しおさい
    if any(x in name for x in ["わかしお", "さざなみ", "しおさい"]): return base_url + "express/wakashio_sazanami.html"
    # 踊り子・湘南
    if "E257" in model or any(x in name for x in ["踊り子", "湘南"]): return base_url + "express/odoriko.html"
    # いなほ・しらゆき
    if "E653" in model or any(x in name for x in ["いなほ", "しらゆき"]): return base_url + "express/inaho.html"
    # つがる
    if "つがる" in name: return base_url + "express/tsugaru.html"
    
    # 新幹線
    if "H5" in model: return "https://www.jrhokkaido.co.jp/train/shinkansen.html"
    if "W7" in model: return "https://www.jr-odekake.net/railroad/train/e7_w7/"
    if "E5" in model: return base_url + "shinkan/e5.html"
    if "E6" in model: return base_url + "shinkan/e6.html"
    if "E7" in model: return base_url + "shinkan/e7.html"
    if "E8" in model: return base_url + "shinkan/e8.html"
    if "E3" in model: return base_url + "shinkan/e3.html"
    if "E2" in model: return base_url + "shinkan/e2.html"
    
    return "https://www.jreast.co.jp/railway/train/#express"

def get_model_style(p):
    # 背景色と文字色の設定 (ユーザー指定)
    styles = {
        "E2系": "background: #ffffff; color: #ff69b4; border: 1px solid #ff69b4;",
        "E3系": "background: #472962; color: #ff0000;", # おしどりパープルに赤
        "E5系": "background: #007b43; color: #ff69b4;", # 常盤グリーンにピンク
        "H5系": "background: #007b43; color: #800080;", # 常盤グリーンに紫
        "E7系": "background: #005cb3; color: #ffa500;", # 瑠璃色にオレンジ
        "W7系": "background: #005cb3; color: #ffa500;", # W7もE7同様
        "E8系": "background: #412a60; color: #ffa500;", # おしどりパープルにオレンジ
        "E6系": "background: #b3304b; color: #ffffff;", # 茜色に白
    }
    return styles.get(p, "")

def render_train(t, station_map_url=""):
    # ◆マークの付与
    diamond = "◆" if t.get('is_diamond') else ""
    op_str = t.get('operation', '◯')
    url = t.get('url', '#')
    name = t.get('train_name', '')
    section = t.get('section', '')
    pf = t.get('platform', '')
    model = t.get('train_model', '')
    
    # 時刻構築
    # ... (省略)
    date_str = t.get('target_date', '')
    arr = t.get('arrival_time')
    dep = t.get('departure_time')
    
    time_content = ""
    if arr and dep:
        time_content = f"<span class='time-val'>{arr}</span><span class='time-sub'>着</span> <span class='time-val'>{dep}</span><span class='time-sub'>発</span>"
    elif arr:
        time_content = f"<span class='time-val'>{arr}</span><span class='time-sub'>着</span>"
    elif dep:
        time_content = f"<span class='time-val'>{dep}</span><span class='time-sub'>発</span>"
    else:
        legacy_time = t.get('time', '')
        legacy_type = t.get('arr_dep', '発')
        time_content = f"<span class='time-val'>{legacy_time}</span><span class='time-sub'>{legacy_type}</span>"

    # 始発・終着アイコン
    icons = ""
    if t.get('is_origin'):
        icons += "<span class='icon-origin' title='当駅始発'>始</span>"
    if t.get('is_destination'):
        icons += "<span class='icon-dest' title='当駅止まり'>終</span>"

    # 時刻カラムを詳細リンクにする
    time_html = f"<div class='time-link-container'>"
    time_html += f"<a href='{url}' class='time-link' target='_blank'>"
    if date_str:
        time_html += f"<span class='date-label'>{date_str}</span><br>"
    time_html += time_content
    time_html += "</a>"
    if icons:
        time_html += f"<div class='time-icons'>{icons}</div>"
    if diamond:
        time_html += f" <span class='diamond'>{diamond}</span>"
    time_html += "</div>"

    # 路線リンク
    # ... (省略)
    route_links = t.get('route_links', [])
    if route_links:
        link_parts = []
        for link in route_links:
            r_name = link.get('name', '')
            r_url = link.get('url', '')
            if r_url:
                link_parts.append(f"<a href='{r_url}' class='route-link' target='_blank'>{r_name}</a>")
            else:
                link_parts.append(f"<span class='route-text'>{r_name}</span>")
        route_display = " ・ ".join(link_parts)
    else:
        r_display = t.get('route', '')
        r_url = t.get('route_url', '')
        if r_url:
            route_display = f"<a href='{r_url}' class='route-link' target='_blank'>{r_display}</a>"
        else:
            route_display = f"<span class='route-text'>{r_display}</span>"

    # バッジ判定
    badge_class = "badge-default"
    shinkansen_names = ["はやぶさ", "こまち", "あさま", "かがやき", "はくたか", "やまびこ", "なすの", "つばさ", "たにがわ", "つるぎ"]
    limited_express_names = ["ひたち", "ときわ", "あずさ", "かいじ", "わかしお", "さざなみ", "しおさい", "踊り子", "湘南", "成田エクスプレス", "いなほ", "しらゆき", "つがる", "草津・四万", "あかぎ", "富士回遊", "サフィール踊り子"]
    
    if "新幹線" in name or any(n in name for n in shinkansen_names):
        badge_class = "badge-shinkansen"
    elif "特急" in name or any(n in name for n in limited_express_names):
        badge_class = "badge-limited-express"

    # 車両表示のリンク処理
    model_html = ""
    if model and model != "不明":
        def make_link(m_name):
            inf_url = get_train_info_url(m_name, name)
            custom_style = get_model_style(m_name)
            style_attr = f" style='{custom_style}'" if custom_style else ""
            return f"<a href='{inf_url}' class='model-tag' target='_blank'{style_attr}>{m_name}</a>"

        # 連結・特定不能ロジック
        coupled_groups = model.split('・')
        rendered_groups = []
        for group in coupled_groups:
            model_parts = re.findall(r'[A-Za-z0-9]+系', group)
            if not model_parts:
                model_parts = [p.strip() for p in re.split(r'[/／]', group) if p.strip()]
            links = [make_link(p) for p in model_parts if p.strip()]
            if links:
                rendered_groups.append("／".join(links))
        model_html = "・".join(rendered_groups)
    
    # 列車名のリンク
    if model_html:
        name_display = f"<span class='badge {badge_class}'>{name}</span>"
    else:
        inf_url = get_train_info_url("", name)
        name_display = f"<a href='{inf_url}' class='train-name-link' target='_blank'><span class='badge {badge_class}'>{name}</span></a>"

    # フィルタ用の時刻データ (HH:MM -> minutes)
    def to_min(t_str):
        if not t_str or ':' not in t_str: return 9999
        h, m = t_str.split(':')
        return int(h) * 60 + int(m)
    
    arr_min = to_min(arr)
    dep_min = to_min(dep)

    # 番線リンク作成
    pf_display = f"<span class='pf-badge'>{pf}</span>"
    if pf and station_map_url:
        pf_display = f"<a href='{station_map_url}' class='pf-link' target='_blank'>{pf_display}</a>"

    html = f"""
        <tr class='train-row' data-arr-min='{arr_min}' data-dep-min='{dep_min}' data-pf='{pf}'>
            <td class='time-cell'>{time_html}</td>
            <td class='pf-cell'>{pf_display}</td>
            <td class='name-cell'>
                {name_display}
                {model_html}
            </td>
            <td class='route-cell'>{route_display}</td>
            <td class='section-cell'>{section}</td>
            <td class='op-cell'><span class='op-{ "ok" if op_str == "◯" else "ng" }'>{op_str}</span></td>
        </tr>
    """
    return html

def render_noriba(n, station_map_url=""):
    pf = n.get('platform', '-')
    route_display = n.get('route', '')
    links = n.get('links', [])
    
    pf_display = f"<span class='noriba-pf'>{pf}</span>"
    if pf != '-' and station_map_url:
        pf_display = f"<a href='{station_map_url}' class='pf-link' target='_blank'>{pf_display}</a>"

    link_html_list = []
    if links:
        for link in links:
            name = link.get('name', route_display)
            url = link.get('url', '#')
            link_text = name
            if "（" in name and "）" in name:
                link_text = name.split("（")[1].split("）")[0] + "時刻表"
            link_html_list.append(f"<a href='{url}' class='noriba-link' target='_blank'>{link_text}</a>")
        route_links = " ".join(link_html_list)
    else:
        route_url = n.get('route_url', '')
        route_links = f"<a href='{route_url}' class='noriba-link' target='_blank'>時刻表</a>" if route_url else "-"

    return f"""
        <li class='noriba-item'>
            {pf_display}
            <div class='noriba-info'>
                <span class='noriba-route'>{route_display}</span>
                <div class='noriba-links'>{route_links}</div>
            </div>
        </li>
    """

def generate_html(req_name, title, description, train_list):
    def get_sort_key(t):
        full_date_str = t.get('target_date', '0/0')
        date_part = full_date_str.split('(')[0]
        m = re.search(r'(\d+)/(\d+)', date_part)
        month_day = f"{m.group(1).zfill(2)}{m.group(2).zfill(2)}" if m else "0000"
        
        time_text = t.get('time', '99:99')
        if t.get('arrival_time'): time_text = t.get('arrival_time')
        elif t.get('departure_time'): time_text = t.get('departure_time')
            
        hour = time_text.split(':')[0]
        if hour.isdigit() and int(hour) < 4:
            time_key = f"2{hour}:{time_text.split(':')[1]}" 
        else:
            time_key = time_text
        return f"{month_day}_{time_key}"
        
    # 駅構内図のURL判定
    station_map_url = ""
    if "東京駅" in title:
        station_map_url = "https://www.jreast.co.jp/estation/stations/1039.html"
    elif "盛岡駅" in title:
        station_map_url = "https://www.jreast.co.jp/estation/stations/1565.html"
    elif "大宮駅" in title:
        station_map_url = "https://www.jreast.co.jp/estation/stations/350.html"

    # タイトルから特定の文言を削除
    display_title = title.replace("(東海道新幹線除く)", "").strip()

    shinkansen_list = [t for t in train_list if not t.get('is_local')]
    noriba_list = [t for t in train_list if t.get('is_noriba')]
    shinkansen_list.sort(key=get_sort_key)
    noriba_list.sort(key=lambda x: str(x.get('platform', '99')).zfill(2))

    # ユニークな番線を抽出 (フィルタ用) と 路線名のマッピング
    pf_to_routes = {}
    for t in shinkansen_list:
        pf = str(t.get('platform', ''))
        if not pf: continue
        if pf not in pf_to_routes:
            pf_to_routes[pf] = set()
        
        # 路線名を取得 (連結の場合は分割)
        r_name = t.get('route', '')
        for part in r_name.split('・'):
            pf_to_routes[pf].add(part.strip())

    def pf_sort_key(s):
        s_norm = unicodedata.normalize('NFKC', str(s))
        m = re.search(r'\d+', s_norm)
        if m:
            return (0, int(m.group()))
        return (1, s)
        
    platforms = sorted(pf_to_routes.keys(), key=pf_sort_key)
    
    # フィルター用のHTML生成 (番線 + 路線名)
    pf_options_html = ""
    for p in platforms:
        routes_text = "、".join(sorted(list(pf_to_routes[p])))
        # 数字を太字にする
        p_bold = re.sub(r'(\d+)', r'<strong>\1</strong>', p)
        # ユーザーの要望に合わせて「番線」を削除
        label = f"{p_bold} {routes_text}" if routes_text else p_bold
        pf_options_html += f"<label class='filter-option'><input type='checkbox' value='{p}' checked> {label}</label>"

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Noto+Sans+JP:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary-color: #0073e6;
            --shinkansen-color: #1a1a1a;
            --limited-express-color: #e60012;
            --bg-color: #f4f7f9;
            --card-bg: #ffffff;
            --text-main: #333333;
            --text-sub: #666666;
            --border-color: #e0e6ed;
            --hover-bg: #f0f7ff;
        }}
        
        /* ... (一部省略) ... */
        body {{ 
            font-family: 'Inter', 'Noto Sans JP', sans-serif; 
            padding: 0; 
            margin: 0;
            background-color: var(--bg-color); 
            color: var(--text-main);
            line-height: 1.6; 
        }}
        
        .container {{
            max-width: 1200px;
            margin: 20px auto;
            padding: 0 16px;
        }}
        
        .header {{
            background: linear-gradient(135deg, #b3304b 0%, #d63d5a 100%); /* E6系 茜色 */
            color: white;
            padding: 8px 16px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 15px;
            border-bottom: 3px solid #f5f5f5; /* 飛雲ホワイトイメージ */
        }}
        
        .header h1 {{ margin: 0; font-size: 1.1rem; font-weight: 700; letter-spacing: -0.01em; line-height: 1.2; }}
        .header p {{ margin: 1px 0 0 0; opacity: 0.9; font-size: 0.8rem; font-weight: 400; }}
        
        .filters {{
            background: white;
            padding: 15px 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 20px;
            border: 1px solid var(--border-color);
        }}
        .filter-item {{ display: flex; align-items: center; gap: 8px; font-weight: 600; color: var(--text-main); cursor: pointer; }}
        .filter-item input {{ width: 18px; height: 18px; cursor: pointer; }}

        h2 {{ 
            font-size: 1.5rem; 
            margin: 40px 0 20px 0; 
            display: flex; 
            align-items: center; 
        }}
        h2::before {{
            content: '';
            display: inline-block;
            width: 4px;
            height: 24px;
            background-color: var(--primary-color);
            margin-right: 12px;
            border-radius: 2px;
        }}
        
        .card {{
            background: var(--card-bg);
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            overflow: visible; /* ポップアップ表示のため */
            border: 1px solid var(--border-color);
        }}
        
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ 
            background-color: #f8f9fa; 
            color: var(--text-sub); 
            font-weight: 600; 
            text-align: left; 
            padding: 16px;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 2px solid var(--border-color);
            position: relative;
        }}
        
        td {{ padding: 16px; border-bottom: 1px solid var(--border-color); vertical-align: middle; }}
        .train-row:hover {{ background-color: var(--hover-bg); transition: background 0.2s; }}
        
        .time-cell {{ min-width: 160px; }}
        .date-label {{ font-size: 0.75rem; color: var(--text-sub); font-weight: 600; }}
        .time-val {{ font-size: 1.2rem; font-weight: 700; color: var(--primary-color); }}
        .time-sub {{ font-size: 0.8rem; color: var(--text-sub); margin-left: 2px; margin-right: 8px; }}
        
        .icon-origin, .icon-dest {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 18px;
            height: 18px;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 700;
            margin-left: 4px;
            vertical-align: middle;
        }}
        .icon-origin {{ background: #e6fffa; color: #2c7a7b; border: 1px solid #81e6d9; }}
        .icon-dest {{ background: #fff5f5; color: #c53030; border: 1px solid #feb2b2; }}
        
        .time-link {{ text-decoration: none; color: inherit; display: inline-block; }}
        .time-link:hover .time-val {{ color: #0056b3; text-decoration: underline; }}
        .time-link-container {{ display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }}
        .time-icons {{ display: inline-flex; gap: 2px; }}
        
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 700;
            margin-bottom: 6px;
        }}
        .badge-shinkansen {{ background: #eef2f7; color: var(--shinkansen-color); border: 1px solid #d1d9e6; }}
        .badge-limited-express {{ background: #fff1f0; color: var(--limited-express-color); border: 1px solid #ffa39e; }}
        .badge-default {{ background: #f5f5f5; color: #555; border: 1px solid #ddd; }}
        
        .train-name-link {{ text-decoration: none; display: inline-block; transition: opacity 0.2s; }}
        .train-name-link:hover {{ opacity: 0.8; }}
        
        .model-tag {{
            font-size: 0.75rem;
            color: #fff;
            background: #4a5568;
            padding: 4px 10px;
            border-radius: 4px;
            display: inline-block;
            font-weight: 600;
            text-decoration: none;
            margin-right: 4px;
            transition: background 0.2s;
        }}
        .model-tag:hover {{ background: #2d3748; }}
        
        .pf-cell {{ white-space: nowrap; min-width: 80px; }}
        .pf-badge {{
            background: #edf2f7;
            color: #2d3748;
            padding: 4px 10px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 0.9rem;
            display: inline-block;
        }}
        .pf-link {{ text-decoration: none; display: inline-block; }}
        .pf-link:hover .pf-badge {{ background: #e2e8f0; color: var(--primary-color); box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}

        /* 番線フィルターポップアップ */
        .pf-filter-btn {{
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 20px;
            height: 20px;
            margin-left: 4px;
            border-radius: 4px;
            transition: background 0.2s;
            color: #aaa;
        }}
        .pf-filter-btn:hover {{ background: #e2e8f0; color: var(--primary-color); }}
        
        .filter-popup {{
            display: none;
            position: absolute;
            top: 100%;
            left: 0;
            z-index: 100;
            background: white;
            border: 1px solid var(--border-color);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            border-radius: 8px;
            padding: 12px;
            min-width: 300px;
        }}
        .filter-popup.active {{ display: block; }}
        .filter-option {{ display: flex; align-items: center; gap: 8px; padding: 6px 0; cursor: pointer; text-transform: none; letter-spacing: normal; font-size: 0.85rem; color: var(--text-main); font-weight: normal; border-bottom: 1px solid #f9f9f9; white-space: nowrap; }}
        .filter-option:last-child {{ border-bottom: none; }}
        .filter-option input {{ margin: 0; flex-shrink: 0; }}
        .filter-actions {{ border-top: 1px solid #eee; margin-top: 8px; padding-top: 8px; display: flex; justify-content: space-between; gap: 8px; }}
        .filter-actions button {{ font-size: 0.75rem; padding: 4px 8px; cursor: pointer; border: 1px solid #ddd; background: #f8f9fa; border-radius: 4px; }}
        .filter-actions button:hover {{ background: #e2e8f0; }}

        .op-ok {{ color: #38a169; font-size: 1.2rem; }}
        .op-ng {{ color: #e53e3e; font-size: 1.2rem; }}
        
        .route-link {{ color: var(--primary-color); text-decoration: none; font-weight: 600; }}
        .route-link:hover {{ text-decoration: underline; }}
        
        .noriba-list {{ list-style: none; padding: 0; margin: 0; }}
        .noriba-item {{ 
            display: flex; 
            align-items: center; 
            padding: 20px; 
            border-bottom: 1px solid var(--border-color); 
        }}
        .noriba-item:last-child {{ border-bottom: none; }}
        .noriba-pf {{
            min-width: 48px;
            height: 48px;
            padding: 0 12px;
            background: var(--primary-color);
            color: white;
            border-radius: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 1rem;
            margin-right: 20px;
            flex-shrink: 0;
            white-space: nowrap;
            box-sizing: border-box;
        }}
        .pf-link:hover .noriba-pf {{ background: #0056b3; transform: scale(1.05); }}

        .noriba-route {{ font-weight: 700; font-size: 1.1rem; display: block; margin-bottom: 6px; }}
        .noriba-link {{
            color: var(--primary-color);
            background: #eef6ff;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 0.85rem;
            margin-right: 10px;
            text-decoration: none;
            display: inline-block;
            margin-top: 4px;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{ font-size: 1.5rem; }}
            th:nth-child(4), td:nth-child(4),
            th:nth-child(5), td:nth-child(5) {{ display: none; }}
            .time-cell {{ min-width: 120px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>{display_title}</h1>
            <p>{description}</p>
        </header>

        <div class="filters">
            <label class="filter-item">
                <input type="checkbox" id="timeFilter">
                <span>現在時刻より10分以上前を隠す</span>
            </label>
        </div>
        
        <section>
            <h2>新幹線・特急列車</h2>
            <div class="card">
                <table id="trainTable">
                    <thead>
                        <tr>
                            <th>時刻</th>
                            <th>
                                <span>番線</span>
                                <span class="pf-filter-btn" id="pfFilterBtn">▼</span>
                                <div class="filter-popup" id="pfFilterPopup">
                                    <div id="pfOptions">
                                        {pf_options_html}
                                    </div>
                                    <div class="filter-actions">
                                        <button id="pfAll">すべて</button>
                                        <button id="pfNone">解除</button>
                                    </div>
                                </div>
                            </th>
                            <th>列車名 / 車両</th>
                            <th>路線</th>
                            <th>区間</th>
                            <th>運行</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    for t in shinkansen_list:
        html += render_train(t, station_map_url)
        
    html += f"""
                    </tbody>
                </table>
            </div>
        </section>
    """
    
    if noriba_list:
        html += f"""
        <section>
            <h2>普通・快速電車等（のりば案内）</h2>
            <div class="card">
                <ul class="noriba-list">
        """
        for n in noriba_list:
            html += render_noriba(n, station_map_url)
        html += f"""
                </ul>
            </div>
        </section>
        """
        
    html += f"""
    </div>
    <footer style="text-align: center; padding: 40px; color: #999; font-size: 0.8rem;">
        &copy; 2026 Train Timetable Generator
    </footer>

    <script>
        document.addEventListener('DOMContentLoaded', () => {{
            const timeFilter = document.getElementById('timeFilter');
            const pfFilterBtn = document.getElementById('pfFilterBtn');
            const pfFilterPopup = document.getElementById('pfFilterPopup');
            const pfOptions = document.getElementById('pfOptions');
            const pfAll = document.getElementById('pfAll');
            const pfNone = document.getElementById('pfNone');
            const trainRows = document.querySelectorAll('.train-row');

            const STORAGE_KEY_TIME = 'timetable_{req_name}_timeFilter';
            const STORAGE_KEY_PF = 'timetable_{req_name}_pfFilter';

            function saveSettings() {{
                localStorage.setItem(STORAGE_KEY_TIME, timeFilter.checked ? '1' : '0');
                const checkedPfs = Array.from(pfOptions.querySelectorAll('input:checked')).map(i => i.value);
                localStorage.setItem(STORAGE_KEY_PF, JSON.stringify(checkedPfs));
            }}

            function loadSettings() {{
                const savedTime = localStorage.getItem(STORAGE_KEY_TIME);
                if (savedTime !== null) {{
                    timeFilter.checked = (savedTime === '1');
                }}

                const savedPf = localStorage.getItem(STORAGE_KEY_PF);
                if (savedPf !== null) {{
                    try {{
                        const checkedPfs = JSON.parse(savedPf);
                        pfOptions.querySelectorAll('input').forEach(input => {{
                            input.checked = checkedPfs.includes(input.value);
                        }});
                    }} catch (e) {{
                        console.error('Failed to load PF settings', e);
                    }}
                }}
            }}

            function applyFilters() {{
                const now = new Date();
                const nowMin = now.getHours() * 60 + now.getMinutes();
                const isTimeFilterActive = timeFilter.checked;
                
                const activePlatforms = Array.from(pfOptions.querySelectorAll('input:checked')).map(i => i.value);

                trainRows.forEach(row => {{
                    const arrMin = parseInt(row.dataset.arrMin);
                    const depMin = parseInt(row.dataset.depMin);
                    const pf = row.dataset.pf;
                    
                    let timeOk = true;
                    if (isTimeFilterActive) {{
                        const targetMin = Math.max(arrMin === 9999 ? -1 : arrMin, depMin === 9999 ? -1 : depMin);
                        if (targetMin !== -1 && targetMin < nowMin - 10) {{
                            timeOk = false;
                        }}
                    }}

                    let pfOk = activePlatforms.includes(pf) || pf === "";

                    if (timeOk && pfOk) {{
                        row.style.display = '';
                    }} else {{
                        row.style.display = 'none';
                    }}
                }});
                
                saveSettings();
            }}

            timeFilter.addEventListener('change', applyFilters);
            pfOptions.addEventListener('change', applyFilters);

            pfFilterBtn.addEventListener('click', (e) => {{
                e.stopPropagation();
                pfFilterPopup.classList.toggle('active');
            }});

            document.addEventListener('click', (e) => {{
                if (!pfFilterPopup.contains(e.target) && e.target !== pfFilterBtn) {{
                    pfFilterPopup.classList.remove('active');
                }}
            }});

            pfAll.addEventListener('click', () => {{
                pfOptions.querySelectorAll('input').forEach(i => i.checked = true);
                applyFilters();
            }});

            pfNone.addEventListener('click', () => {{
                pfOptions.querySelectorAll('input').forEach(i => i.checked = false);
                applyFilters();
            }});

            // 初期化
            loadSettings();
            applyFilters();
        }});
    </script>
</body>
</html>
"""
    filename = f"timetable_{req_name}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generated {filename}")

def main():
    if not os.path.exists("results.json"):
        print("results.jsonが見つかりません。")
        return
        
    with open("results.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # Req1
    generate_html("req1", "1. 東京駅発着 新幹線・特急 (東海道新幹線除く)", "3/29(日) 14:00〜17:00", data.get("req1", []))
    
    # Req2
    generate_html("req2", "2. 大宮駅発着 新幹線・特急", "3/29(日) 15:00〜3/31(火) 15:00", data.get("req2", []))
    
    # Req3
    generate_html("req3", "3. 盛岡駅発着 新幹線・特急", "3/31(火) 14:00〜4/1(水) 14:00", data.get("req3", []))
    
    # Req4
    generate_html("req4", "4. 東京駅発着 新幹線・特急 (東海道新幹線除く)", "4/1(水) 13:00〜16:00", data.get("req4", []))

if __name__ == "__main__":
    main()
