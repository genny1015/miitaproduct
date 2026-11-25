import os
import random
import time
import requests

# ================= 1. 環境變數設定 =================
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
THREADS_USER_ID = os.environ["THREADS_USER_ID"]
THREADS_ACCESS_TOKEN = os.environ["THREADS_ACCESS_TOKEN"]

# 若要同時發 IG，請填入以下三個值（沒填則只自動發 Threads）
IG_USER_ID = os.environ.get("IG_USER_ID", "")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", "")
PRODUCT_IMAGE_URL = os.environ.get("PRODUCT_IMAGE_URL", "")  # 官網熱感衣圖片公開網址

PRODUCT_URL = "https://miitamed.com/shop/heartwear/?utm_source=social_auto&utm_medium=ai_post&utm_campaign=heartwear"

ANGLES = [
    "晚上蓋厚被子還是手腳冰冷，直接把遠紅外線熱感衣當暖睡衣穿，不靠厚重堆疊也能一夜好眠",
    "台灣早晚溫差大，早上出門防寒、進辦公室脫外套依然輕薄俐落不臃腫",
    "一件抵兩件：白天是隱形發熱打底衣，晚上直接當居家放鬆睡眠衣",
    "台灣製造、男女同款，幫另一半或怕冷的家人長輩一起準備，親膚無負擔"
]


# ================= 2. 免費 Gemini API 自動寫高轉換文案 =================
def generate_promo_copy() -> str:
    angle = random.choice(ANGLES)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

    prompt = f"""
你是一位台灣機能服飾品牌行銷企劃，請為「MiiTA 醫創達 遠紅外線熱感衣」寫一篇能讓人想直接點擊下單的社群貼文。

【本次主打切角】：{angle}
【產品核心賣點】：
- 遠紅外線熱感布料，溫和蓄熱不悶汗
- 台灣製造、男女同款
- 日常穿搭＋夜間睡眠兩用

【撰寫規則】：
1. 開頭第一句直接戳中怕冷或睡不好的痛點（吸引人停下來看）。
2. 中間自然帶出這件「遠紅外線熱感衣」為什麼跟一般發熱衣不同（白天打底、晚上可直接當睡衣）。
3. 結尾放上明確行動呼籲與商品下單網址：{PRODUCT_URL}
4. 字數控制在 130~180 字，台灣自然口語、有說服力，文末加 2 個相關 hashtag 即可。不要輸出任何前言或標題，直接給貼文內容。
"""
    resp = requests.post(url, json={
        "contents": [{"parts": [{"text": prompt}]}]
    }).json()

    return resp["candidates"][0]["content"]["parts"][0]["text"].strip()


# ================= 3. 自動發布到 Threads =================
def post_to_threads(text: str):
    create_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
    create_res = requests.post(create_url, data={
        "media_type": "TEXT",
        "text": text,
        "access_token": THREADS_ACCESS_TOKEN
    }).json()

    creation_id = create_res.get("id")
    if not creation_id:
        raise RuntimeError(f"Threads 建立貼文失敗：{create_res}")

    time.sleep(3)

    pub_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish"
    pub_res = requests.post(pub_url, data={
        "creation_id": creation_id,
        "access_token": THREADS_ACCESS_TOKEN
    }).json()
    print("✅ Threads 自動發文成功：", pub_res)


# ================= 4. 同步發布圖文到 IG（若有設定圖片網址） =================
def post_to_ig(caption: str):
    if not (IG_USER_ID and META_ACCESS_TOKEN and PRODUCT_IMAGE_URL):
        return

    create_url = f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media"
    create_res = requests.post(create_url, data={
        "image_url": PRODUCT_IMAGE_URL,
        "caption": caption,
        "access_token": META_ACCESS_TOKEN
    }).json()

    creation_id = create_res.get("id")
    if not creation_id:
        raise RuntimeError(f"IG 建立貼文失敗：{create_res}")

    time.sleep(5)

    pub_url = f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media_publish"
    pub_res = requests.post(pub_url, data={
        "creation_id": creation_id,
        "access_token": META_ACCESS_TOKEN
    }).json()
    print("✅ IG 自動發文成功：", pub_res)


if __name__ == "__main__":
    copy_text = generate_promo_copy()
    print("📝 本次 AI 生成文案：\n", copy_text)
    post_to_threads(copy_text)
    post_to_ig(copy_text)
