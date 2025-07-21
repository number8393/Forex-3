import time
import requests
import yfinance as yf
import pytz
from datetime import datetime
from statistics import mean

CMC_API_KEY = "69c96f60-ca43-480a-83a0-63cdb2c43fb3"
TG_TOKEN = "7533119295:AAG_Hnudjc4hF4ZthROX2_smvvSJ1hk3k6o"
TG_CHAT_ID = "5556108366"

CRYPTO_PAIRS = [
    "BTC-USD", "ETH-USD", "BNB-USD", "XRP-USD", "SOL-USD",
    "DOGE-USD", "ADA-USD", "DOT-USD", "AVAX-USD"
    # "MATIC-USD" — временно исключено (ошибка загрузки)
]

def get_volume_analysis(data):
    try:
        volumes = data['Volume'].tail(10)
        if volumes.empty:
            return "Нет данных"
        avg_volume = volumes.mean()
        current_volume = volumes.iloc[-1]
        return "🔥 Повышенный интерес" if current_volume > avg_volume * 1.2 else "📉 Средний интерес"
    except:
        return "⚠️ Ошибка объема"

def get_candle_signal(data):
    try:
        if data.shape[0] < 3:
            return "Недостаточно данных"
        last = data.tail(2)
        c1, o1 = float(last.iloc[-1]['Close']), float(last.iloc[-1]['Open'])
        c2, o2 = float(last.iloc[-2]['Close']), float(last.iloc[-2]['Open'])

        if c1 > o1 and c2 < o2:
            return "🚀 Бычий разворот"
        elif c1 < o1 and c2 > o2:
            return "🐻 Медвежий разворот"
        else:
            return "❌ Сигналов нет"
    except:
        return "❌ Ошибка анализа"

def get_confidence(data):
    try:
        if data.empty or len(data) < 5:
            return 0
        return round(abs(data['Close'].pct_change().tail(5).mean()) * 100, 2)
    except:
        return 0

def get_news_time():
    headers = {'X-CMC_PRO_API_KEY': CMC_API_KEY}
    try:
        r = requests.get('https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest', headers=headers, timeout=10)
        if r.status_code == 200:
            now = datetime.now(pytz.utc)
            hour = now.hour
            if 11 <= hour <= 13 or 16 <= hour <= 22:
                return "🟢 Новости стабильны. Спокойная торговля с 11:00 до 13:00 и с 16:00 до 22:00"
            else:
                return "🟡 Новости стабильны, но сейчас не пиковое время"
        else:
            return "🔴 Новости нестабильны"
    except:
        return "⚠️ Новости недоступны"

def get_signal(pair):
    try:
        data = yf.download(pair, period="2d", interval="1h", progress=False)
        if data.empty or data['Close'].isnull().all():
            return None

        signal = get_candle_signal(data)
        if "Сигналов нет" in signal or "Ошибка" in signal:
            return None

        trend = "📈 Рост" if data['Close'].iloc[-1] > data['Close'].iloc[-5] else "📉 Падение"
        price_now = float(data['Close'].iloc[-1])
        confidence = get_confidence(data)
        duration = 5 if confidence < 0.5 else 15

        return {
            "pair": pair,
            "price": price_now,
            "signal": signal,
            "volume": get_volume_analysis(data),
            "trend": trend,
            "confidence": confidence,
            "duration": duration
        }
    except:
        return None

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=payload, timeout=10)
    except:
        pass

def main():
    while True:
        try:
            news_status = get_news_time()
            for pair in CRYPTO_PAIRS:
                result = get_signal(pair)
                if result:
                    message = (
                        f"🔔 <b>Сигнал для: {result['pair']}</b>\n"
                        f"💰 Цена: {result['price']:.2f}$\n"
                        f"🕯 Свечи: {result['signal']}\n"
                        f"📊 Объем: {result['volume']}\n"
                        f"📉 Тренд: {result['trend']}\n"
                        f"🎯 Уверенность: {result['confidence']}%\n"
                        f"⏱ Сделка: {result['duration']} мин\n"
                        f"🧠 Smart Money / SmokeFX активны\n"
                        f"📆 {news_status}"
                    )
                    send_telegram_message(message)
                else:
                    send_telegram_message(f"🔍 {pair}: нет подходящих сигналов ⏳")
            time.sleep(60)
        except Exception as e:
            send_telegram_message(f"❌ Ошибка в основном цикле: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
