import requests
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
import os
import re

token = os.environ.get("LINE_NOTIFY_TOKEN")

app = Flask(__name__)


nthu2020_url1 = "http://140.114.188.57/nthu2020/fn1/kw1.aspx"
nthu2020_url2 = "http://140.114.188.57/nthu2020/fn1/kw2.aspx"
nthu2020_url3 = "http://140.114.188.57/nthu2020/fn1/kw3.aspx"
power1_capacity = 5200
power2_capacity = 5600
power3_capacity = 1500

station_dict = [
    {
        "station":"北區一號",
        "url":nthu2020_url1,
        "capacity":power1_capacity
    },
    {
        "station":"北區二號",
        "url":nthu2020_url2,
        "capacity":power2_capacity
    },
    {
        "station":"仙宮",
        "url":nthu2020_url3,
        "capacity":power3_capacity
    }
]

def get_kw_value(url):
    response = requests.get(url)

    if response.status_code == 200:
        # 使用正則表達找到"kW: "後面的数字
        pattern = r'kW: (-?\d.*?\d+)'
        match = re.search(pattern, response.text)
        
        if match:
            kw_value = match.group(1)
            # 去掉逗號
            kw_value = kw_value.replace(',', '')
            return float(kw_value)
        else:
            print("未找到匹配的kW值")
    else:
        print(f"請求失敗，狀態碼：{response.status_code}")

def get_overload_list():
    overload_list = []
    
    for station_info in station_dict:
        url = station_info["url"]
        capacity = station_info["capacity"]
        
        try:
            kw_value = get_kw_value(url)
        except Exception as e:
            print(f"發生異常: {e}")
            continue

        if kw_value is not None and (kw_value / capacity) > 0.9:
            load = round(kw_value / capacity * 100, 1)
            load_percent = f'{load:.1f}%'
            overload_list.append({"station": station_info["station"], "loading": load_percent})

    return overload_list


def send_line_notification(token, msg):
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    params = {
        "message": msg
    }
    r = requests.post("https://notify-api.line.me/api/notify", headers=headers, params=params)

def job():
    # token = ""
    overload_list = get_overload_list()
    if len(overload_list) > 0:
        for overload_station in overload_list:
            station = overload_station['station']
            current_load = overload_station['loading']
            send_line_notification(token, f"\n變電站:{station} \n目前負載: {current_load}\n*聽說北區一號達到130%會停電")

scheduler = BackgroundScheduler()
scheduler.add_job(job, 'interval', minutes=1)
scheduler.start()

@app.route('/')
def home():
    return "Power Monitor Flask App with APScheduler is running."

if __name__ == "__main__":
    app.run(debug=True)
    # job()
