from flask import Flask, render_template_string
import requests
from bs4 import BeautifulSoup
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import concurrent.futures

app = Flask(__name__)

# 定義抓取數據的函數
def scrape_data(url, data_ids):
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("http://", adapter)
    http.mount("https://", adapter)
    try:
        response = http.get(url, timeout=5)  # 將超時時間設置為5秒
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        data = {}
        for data_id in data_ids:
            element = soup.find('span', id=data_id)
            data[data_id] = element.text if element else f"找不到 id 為 {data_id} 的 span 元素"
        return data
    except requests.exceptions.RequestException as e:
        return {data_id: f"Error occurred: {e}" for data_id in data_ids}

def scrape_data_parallel(targets):
    data_list = []
    
    def fetch_data(target):
        return scrape_data(target['url'], target['data_ids'])
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch_data, target) for target in targets]
        for future in concurrent.futures.as_completed(futures):
            data_list.append(future.result())
    
    return data_list

# 定義路由和視圖函數
@app.route('/')
def index():
    targets = [
        {
            'url': 'http://tienching.ipvita.net/InstantPower.aspx?gw6UXnBQFxQcqRQvH_s-Zw&lang=traditional_chinese&time=0',
            'data_ids': ['lbl_online_date', 'lbl_daily_pw', 'lbl_today_price', 'lbl_total_price', 'lbl_system_time']
        },
        {
            'url': 'http://tienching.ipvita.net/InstantPower.aspx?9SGSfISfMFauB-qNFJwe2w&lang=traditional_chinese&time=',
            'data_ids': ['lbl_online_date', 'lbl_daily_pw', 'lbl_today_price', 'lbl_total_price', 'lbl_system_time']
        },
        {
            'url': 'http://tienching.ipvita.net/InstantPower.aspx?Us4azBhQh_643NPCj6EZzQ&lang=traditional_chinese&time=0',
            'data_ids': ['lbl_online_date', 'lbl_daily_pw', 'lbl_today_price', 'lbl_total_price', 'lbl_system_time']
        }
    ]

    data_list = scrape_data_parallel(targets)

    id_to_chinese = {
        'lbl_online_date': '系統掛表日期',
        'lbl_daily_pw': '今日發電量kw',
        'lbl_today_price': '今日收入',
        'lbl_total_price': '掛表至今總收入',
        'lbl_system_time': '更新時間',
    }
    html_content = """
    <!doctype html>
    <html lang="zh-tw">
    <head>
        <meta charset="utf-8">
        <title>太陽能三期數據整合</title>
        <style>
            body { font-family: Times New Roman, serif; font-size:20px; margin: 20px; }
            h1 { color: #333; }
            ul { list-style-type: none; padding: 0; }
            li { background: #f4f4f4; margin: 5px 0; padding: 10px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>太陽能三期數據整合</h1>
        {% for data in data_list %}
            <h2>太陽能第{{ loop.index }}期</h2>
            <ul>
                {% for key, value in data.items() %}
                <li>{{ id_to_chinese[key] }}: {{ value }}</li>
                {% endfor %}
            </ul>
        {% endfor %}
    </body>
    </html>
    """

    return render_template_string(html_content, data_list=data_list, id_to_chinese=id_to_chinese)

if __name__ == '__main__':
    app.run(port=5000, debug=True)
