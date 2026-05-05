import sys, re, html

def md_to_cards(md_text, date_str, page_type):
    lines = md_text.strip().split('\n')
    title_line = lines[0]
    meta_match = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)', title_line)
    date_display = meta_match.group(1) if meta_match else date_str

    if page_type == "news":
        nav_icon, nav_label = "\U0001f4f0", "每日要闻"
        nav_peer = f"academic-daily-{date_str}.html"
        peer_icon, peer_label = "\U0001f4da", "学术"
    else:
        nav_icon, nav_label = "\U0001f4da", "学术日报"
        nav_peer = f"daily-news-{date_str}.html"
        peer_icon, peer_label = "\U0001f4f0", "要闻"

    page_title = f"{nav_icon} {nav_label} | {date_display}"

    sections = []
    current_section = None
    current_card = None

    for line in lines[1:]:
        stripped = line.strip()
        if stripped.startswith('## ') and not stripped.startswith('## \U0001f4ca'):
            if current_card and current_section:
                current_section['cards'].append(current_card)
                current_card = None
            if current_section:
                sections.append(current_section)
            sec_title = stripped[3:].strip()
            color_class = ""
            if any(k in sec_title for k in ['财经', '价格', '小米']):
                color_class = ' blue'
            elif any(k in sec_title for k in ['国际', '地缘', '脑机', '医学', '健康', '生命']):
                color_class = ' green'
            elif any(k in sec_title for k in ['国内', '伦理', '教育', '法律']):
                color_class = ' purple'
            elif any(k in sec_title for k in ['其他', '前沿科技']):
                color_class = ' orange'
            current_section = {'title': sec_title, 'color': color_class, 'cards': []}
            continue

        if stripped.startswith('### '):
            if current_card and current_section:
                current_section['cards'].append(current_card)
            card_title = stripped[4:].strip()
            is_star = '\u2b50' in card_title
            card_title_clean = card_title.replace('\u2b50', '').strip()
            current_card = {'title': card_title_clean, 'star': is_star, 'body': '', 'links': []}
            continue

        if current_card is None:
            continue

        if stripped.startswith('\U0001f517'):
            source_text = stripped[1:].strip()
            links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', source_text)
            if links:
                current_card['links'] = links
            continue

        if stripped.startswith('|'):
            current_card['body'] += '\n' + line
            continue

        if stripped.startswith('>'):
            current_card['body'] += '\n' + line
            continue

        if stripped == '---' or stripped == '':
            continue

        if stripped.startswith('## \U0001f4ca'):
            if current_card:
                current_section['cards'].append(current_card)
                current_card = None
            if current_section:
                sections.append(current_section)
            current_section = None
            continue

        if stripped.startswith('*\U0001f4e1') or stripped.startswith('*\U0001f916'):
            continue

        if current_card:
            processed = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', stripped)
            processed = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" style="color:#667eea">\1</a>', processed)
            if current_card['body']:
                current_card['body'] += '<br>' + processed
            else:
                current_card['body'] = processed

    if current_card:
        current_section['cards'].append(current_card)
    if current_section:
        sections.append(current_section)

    html_parts = []
    for sec in sections:
        if sec['title'].startswith('\U0001f4ca'):
            html_parts.append('<div class="summary-box"><h3>\U0001f4ca 本日最大看点</h3><ul>')
            for card in sec['cards']:
                if card['body']:
                    html_parts.append(f'<li>{card["body"]}</li>')
            html_parts.append('</ul></div>')
            continue

        sec_html = f'<div class="section"><div class="section-title{sec["color"]}">{sec["title"]}</div>'

        for card in sec['cards']:
            star = '<span class="star">\u2b50</span>' if card['star'] else ''
            card_html = f'<div class="card"><div class="card-title">{star}{html.escape(card["title"])}</div>'

            body = card['body']
            if '|' in body and body.count('|') > 3:
                table_lines = [l for l in body.split('\n') if l.strip().startswith('|')]
                if len(table_lines) >= 2:
                    card_html += '<div class="card-body">'
                    rows = []
                    for tl in table_lines:
                        tl = tl.strip()
                        if '---' in tl:
                            continue
                        cells = [c.strip() for c in tl.split('|')[1:-1]]
                        rows.append(cells)
                    if rows:
                        card_html += '<table>'
                        for i, row in enumerate(rows):
                            tag = 'th' if i == 0 else 'td'
                            card_html += '<tr>'
                            for cell in row:
                                card_html += f'<{tag}>{cell}</{tag}>'
                            card_html += '</tr>'
                        card_html += '</table>'
                    text_parts = [l for l in body.split('\n') if l.strip() and not l.strip().startswith('|')]
                    extra_text = ' '.join(text_parts).strip()
                    if extra_text and not extra_text.startswith('[') and not extra_text.startswith('<'):
                        card_html += f'<br>{extra_text}'
                    card_html += '</div>'
                else:
                    card_html += f'<div class="card-body">{body}</div>'
            elif body.startswith('>'):
                card_html += f'<div class="card-body" style="margin-top:8px;color:#888;font-size:14.5px;border-left:3px solid #ddd;padding-left:10px;">{body.replace(">", "").replace("\U0001f4a1", "").strip()}</div>'
            else:
                card_html += f'<div class="card-body">{body}</div>'

            if card['links']:
                links_html = ''
                for lbl, url in card['links']:
                    links_html += f'<a href="{url}" target="_blank" rel="noopener" class="source-link">\U0001f517 {html.escape(lbl)}</a>'
                card_html += f'<div class="source-links">{links_html}</div>'

            card_html += '</div>'
            sec_html += card_html

        sec_html += '</div>'
        html_parts.append(sec_html)

    return '\n'.join(html_parts), date_display, nav_icon, nav_label, nav_peer, peer_icon, peer_label, page_title

CSS = """  * { margin: 0; padding: 0; box-sizing: border-box; }
  :root { --bg: #f5f5f5; --card-bg: #fff; --text: #333; --text2: #444; --nav-bg: #1a1a2e; --accent: #e74c3c; --border: #eee; --shadow: rgba(0,0,0,0.08); }
  body.dark-mode { --bg: #1a1a2e; --card-bg: #16213e; --text: #e0e0e0; --text2: #b0b0b0; --nav-bg: #0f0f23; --border: #2a2a4a; --shadow: rgba(0,0,0,0.3); }
  body { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; background: var(--bg); color: var(--text); line-height: 1.7; font-size: 17px; padding: 56px 12px 20px; transition: background .3s, color .3s; -webkit-tap-highlight-color: transparent; }
  .navbar { position: fixed; top: 0; left: 0; right: 0; z-index: 999; background: var(--nav-bg); color: #fff; display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; height: 50px; box-shadow: 0 2px 8px rgba(0,0,0,0.2); }
  .navbar-left, .navbar-right { display: flex; align-items: center; gap: 6px; }
  .nav-btn { display: inline-flex; align-items: center; gap: 4px; background: rgba(255,255,255,0.15); border: none; color: #fff; padding: 6px 12px; border-radius: 18px; font-size: 13.5px; cursor: pointer; text-decoration: none; user-select: none; transition: background .2s; }
  .nav-btn:hover, .nav-btn:active { background: rgba(255,255,255,0.28); }
  .nav-btn:active { transform: scale(0.95); }
  .nav-title { font-size: 15px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 160px; }
  h1 { text-align: center; font-size: 21px; margin-bottom: 4px; }
  .meta { text-align: center; color: #888; font-size: 12.5px; margin-bottom: 16px; }
  .dark-mode .meta { color: #777; }
  .section { background: var(--card-bg); border-radius: 10px; padding: 15px; margin-bottom: 12px; box-shadow: 0 1px 3px var(--shadow); transition: background .3s; }
  .section-title { font-size: 17.5px; font-weight: bold; margin-bottom: 10px; color: var(--text); border-left: 4px solid var(--accent); padding-left: 9px; }
  .section-title.blue { border-color: #3498db; }
  .section-title.green { border-color: #27ae60; }
  .section-title.purple { border-color: #9b59b6; }
  .section-title.orange { border-color: #e67e22; }
  .card { margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid var(--border); }
  .card:last-child { border: none; margin: 0; padding: 0; }
  .card-title { font-weight: bold; font-size: 16px; color: var(--text); margin-bottom: 5px; display: flex; align-items: flex-start; gap: 5px; }
  .star { color: var(--accent); flex-shrink: 0; font-size: 14px; margin-top: 2px; }
  .card-body { color: var(--text2); font-size: 15.5px; }
  .source-links { margin-top: 8px; display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
  .source-link { display: inline-flex; align-items: center; gap: 3px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff !important; text-decoration: none; padding: 4px 11px; border-radius: 14px; font-size: 12px; transition: opacity .2s, transform .15s; white-space: nowrap; max-width: 180px; overflow: hidden; text-overflow: ellipsis; }
  .source-link:hover { opacity: .85; }
  .source-link:active { transform: scale(.95); opacity: 1; }
  .dark-mode .source-link { background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%); }
  table { width: 100%; border-collapse: collapse; margin: 8px 0; font-size: 14.5px; }
  th { background: var(--bg); text-align: left; padding: 7px 9px; font-weight: 600; border-bottom: 2px solid var(--border); }
  td { padding: 6px 9px; border-bottom: 1px solid var(--border); color: var(--text2); }
  .price-highlight { color: var(--accent); font-weight: bold; font-size: 17px; }
  .summary-box { background: #fffbe6; border: 1px solid #ffe58f; border-radius: 8px; padding: 13px; margin: 12px 0; }
  .dark-mode .summary-box { background: #332d00; border-color: #554d00; }
  .summary-box h3 { font-size: 16px; margin-bottom: 7px; color: #856404; }
  .dark-mode .summary-box h3 { color: #f0d060; }
  .summary-box ul { padding-left: 18px; color: #555; }
  .dark-mode .summary-box ul { color: #bbb; }
  .summary-box li { margin-bottom: 3px; font-size: 14.5px; }
  .footer { text-align: center; color: #888; font-size: 11.5px; margin: 16px 0 8px; line-height: 1.6; }
  b { color: var(--text); }
  .back-top { position: fixed; right: 14px; bottom: 70px; z-index: 998; width: 38px; height: 38px; border-radius: 50%; background: var(--accent); color: #fff; display: none; align-items: center; justify-content: center; font-size: 18px; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.25); border: none; user-select: none; transition: transform .2s, opacity .2s; }
  .back-top.show { display: flex; opacity: 0.85; }
  .back-top:active { transform: scale(0.9); opacity: 1; }
  .bottom-bar { position: fixed; bottom: 0; left: 0; right: 0; z-index: 997; background: var(--card-bg); border-top: 1px solid var(--border); display: flex; align-items: center; justify-content: space-around; padding: 8px 0; padding-bottom: max(8px, env(safe-area-inset-bottom)); box-shadow: 0 -1px 6px var(--shadow); }
  .bottom-bar button { display: flex; flex-direction: column; align-items: center; gap: 2px; background: none; border: none; color: var(--text2); font-size: 11px; cursor: pointer; padding: 4px 12px; border-radius: 8px; transition: background .2s, color .2s; user-select: none; }
  .bottom-bar button:active { background: var(--bg); }
  .bottom-bar button .icon { font-size: 20px; }
  .bottom-bar button.active { color: var(--accent); }"""

JS = """function toggleDark() {
  document.body.classList.toggle('dark-mode');
  const isDark = document.body.classList.contains('dark-mode');
  document.getElementById('darkBtn').textContent = isDark ? '\\u2600\\ufe0f' : '\\U0001f319';
  document.getElementById('darkIcon').textContent = isDark ? '\\u2600\\ufe0f' : '\\U0001f319';
  localStorage.setItem('darkMode', isDark ? '1' : '0');
}
if(localStorage.getItem('darkMode')==='1') toggleDark();
const backTop = document.getElementById('backTop');
window.addEventListener('scroll', function() {
  if(window.scrollY > 300) backTop.classList.add('show');
  else backTop.classList.remove('show');
}, {passive:true});
document.getElementById('refreshBtn').addEventListener('click', function() {
  const btn = this; btn.innerHTML = '\\u23f3';
  setTimeout(function() { btn.innerHTML = '\\U0001f504'; location.reload(); }, 300);
});"""

def wrap(content, date_display, nav_icon, nav_label, nav_peer, peer_icon, peer_label, page_title, date_str):
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{page_title}</title>
<style>{CSS}</style>
</head>
<body>
<div class="navbar">
  <div class="navbar-left"><a href="index.html" class="nav-btn">\u2b05 首页</a></div>
  <div class="nav-title">{nav_icon} {nav_label}</div>
  <div class="navbar-right">
    <button class="nav-btn" onclick="location.reload()" id="refreshBtn">\U0001f504</button>
    <button class="nav-btn" onclick="toggleDark()" id="darkBtn">\U0001f319</button>
  </div>
</div>
<h1>{nav_icon} {nav_label}</h1>
<p class="meta">{date_display} | AI/\u79d1\u6280 \u00b7 \u8d22\u7ecf \u00b7 \u5b66\u672f \u00b7 \u56fd\u5185</p>
{content}
<p class="footer">\U0001f4e1 \u6570\u636e\u6765\u6e90\uff1a\u65b0\u6d6a\u8d22\u7ecf / AIToolly / \u592e\u89c6\u7f51 / \u4e2d\u65b0\u7f51 \u7b49<br>\U0001f916 WorkBuddy \u81ea\u52a8\u91c7\u96c6 | {date_str}</p>
<button class="back-top" id="backTop" onclick="window.scrollTo({{top:0,behavior:'smooth'}})">\u2191</button>
<div class="bottom-bar">
  <button onclick="location.href='index.html'"><span class="icon">\U0001f3e0</span>\u9996\u9875</button>
  <button onclick="location.href='{nav_peer}'"><span class="icon">{peer_icon}</span>{peer_label}</button>
  <button onclick="location.reload()"><span class="icon">\U0001f504</span>\u5237\u65b0</button>
  <button onclick="toggleDark()"><span class="icon" id="darkIcon">\U0001f319</span>\u6697\u8272</button>
  <button onclick="window.scrollTo({{top:0,behavior:'smooth'}})"><span class="icon">\u2191</span>\u9876\u90e8</button>
</div>
<script>{JS}</script>
</body></html>"""

date_str = "2026-05-05"

import os
base = os.path.dirname(os.path.abspath(__file__))

for page_type, md_name, html_name in [
    ("news", f"daily-news-{date_str}.md", f"daily-news-{date_str}.html"),
    ("academic", f"academic-daily-{date_str}.md", f"academic-daily-{date_str}.html"),
]:
    md_file = os.path.join(base, md_name)
    html_file = os.path.join(base, html_name)
    with open(md_file, 'r', encoding='utf-8') as f:
        md_text = f.read()
    content, date_display, nav_icon, nav_label, nav_peer, peer_icon, peer_label, page_title = md_to_cards(md_text, date_str, page_type)
    full_html = wrap(content, date_display, nav_icon, nav_label, nav_peer, peer_icon, peer_label, page_title, date_str)
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(full_html)
    print(f"OK: {html_file}")

print("Done!")
