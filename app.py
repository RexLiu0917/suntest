from flask import Flask, render_template_string
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import logging

app = Flask(__name__)

# 設置日誌記錄
logging.basicConfig(level=logging.INFO)

# 定義異步抓取數據的函數
async def fetch(session, url, data_ids):
    try:
        logging.info(f"Fetching data from {url}")
        async with session.get(url, timeout=15) as response:  # 增加超時時間
            response.raise_for_status()
            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
            data = {}
            for data_id in data_ids:
                element = soup.find('span', id=data_id)
                data[data_id] = element.text if element else f"找不到 id 為 {data_id} 的 span 元素"
            logging.info(f"Fetched data: {data}")
            return data
    except aiohttp.ClientError as e:
        logging.error(f"Client error fetching data from {url}: {e}")
        return {data_id: f"Client error occurred: {e}" for data_id in data_ids}
    except asyncio.TimeoutError as e:
        logging.error(f"Timeout error fetching data from {url}: {e}")
        return {data_id: f"Timeout error occurred: {e}" for data_id in data_ids}
    except Exception as e:
        logging.error(f"Unexpected error fetching data from {url}: {e}")
        return {data_id: f"Unexpected error occurred: {e}" for data_id in data_ids}

async def scrape_data(targets):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for target in targets:
            tasks.append(fetch(session, target['url'], target['data_ids']))
        return await asyncio.gather(*tasks)

# 定義路由和視圖函數
@app.route('/')
def index():
    logging.info("Index route accessed")
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

    try:
        data_list = asyncio.run(scrape_data(targets))
    except Exception as e:
        logging.error(f"Error in scrape_data: {e}")
        return f"Error occurred: {e}"

    def get_daily_powers(data_list):
        try:
            return [int(data.get('lbl_daily_pw', '0').replace(',', '')) for data in data_list if data.get('lbl_daily_pw', '0').replace(',', '').isdigit()]
        except Exception as e:
            logging.error(f"Error converting daily powers: {e}")
            return [0]
    
    # 使用函數獲取所有 'lbl_daily_pw' 的值
    daily_powers = get_daily_powers(data_list)
    daily_total_powers = sum(daily_powers)
    
    def get_daily_prices(data_list):
        try:
            return [int(data.get('lbl_today_price', '0').replace(',', '')) for data in data_list if data.get('lbl_today_price', '0').replace(',', '').isdigit()]
        except Exception as e:
            logging.error(f"Error converting daily prices: {e}")
            return [0]
    
    # 使用函數獲取所有 'lbl_today_price' 的值
    daily_prices = get_daily_prices(data_list)
    daily_total_prices = sum(daily_prices)
    
    id_to_chinese = {
        'lbl_online_date': '系統掛表日期',
        'lbl_daily_pw': '今日發電量kwh',
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
        body { 
            font-family: "Times New Roman", serif; 
            font-size: 50px;
            font-weight: bold; 
            background-color: #FAFAD2;
        }
        h1 { 
            color: #FF4500;
            text-align: center;
        }
        h2{
            background-color: #FFDEAD;
            text-align: center;
            margin: 0px;
            padding: 20px;
        }
        ul { 
            list-style-type: none; 
            padding: 0; 
            margin: 0;
        }
        li { 
            background: #FDF5E6; 
            margin: 10px 0; 
            padding: 10px; 
            border-radius: 5px;
            color: #000080; 
        }
        .total-container { 
            display: flex; 
            justify-content: space-around; 
        }
        .total-item { 
            width: 50%; 
            text-align: center; 
        }
        p.at { 
            font-size: 80px; 
            margin: 10px;
            text-align: center; 
            color: #6A5ACD;
        }
        div.area { 
            border: 5px solid #663399;
            border-radius: 10px;
            margin: 30px;  
        }
        div.smallarea{
            padding: 10px;
        }
        div.total-item{
            border: 5px solid #800000;
            margin: 10px;
        }
        </style>
    </head>
    <body>
        <h1>太陽能三期數據整合</h1>
        <div class="total-container">
            <div class="total-item">
                <p>今日發電量總和: </p>
                <p class="at">{{ daily_total_powers }} kwh</p>
            </div>
            <div class="total-item">
                <p>今日收入總和: </p>
                <p class="at">{{ daily_total_prices }} 元</p>
            </div>
        </div>
        {% for data in data_list %}
        <div class="area">
            <h2>太陽能第{{ loop.index }}期</h2>
            <div class="smallarea">
            <ul>
                {% for key, value in data.items() %}
                <li>{{ id_to_chinese[key] }}: {{ value }}</li>
                {% endfor %}
            </ul>
            </div>
        </div>
        {% endfor %}
    </body>
    </html>
    """

    return render_template_string(html_content, data_list=data_list, id_to_chinese=id_to_chinese, daily_total_powers=daily_total_powers, daily_total_prices=daily_total_prices)

if __name__ == '__main__':
    logging.info("Starting Flask app")
    app.run(port=5000, debug=True)
