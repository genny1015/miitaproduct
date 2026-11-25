import os
import random
import time
import requests

# ================= 1. 環境變數與商品設定 =================
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"].strip()
THREADS_USER_ID = os.environ["THREADS_USER_ID"].strip()
THREADS_ACCESS_TOKEN = os.environ["THREADS_ACCESS_TOKEN"].strip()

IG_USER_ID = os.environ.get("IG_USER_ID", "").strip()
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", "").strip()

PRODUCT_URL = "https://miitamed.com/shop/heartwear/?utm_source=social_auto&utm_medium=ai_post&utm_campaign=heartwear"

# Google 雲端硬碟高畫質原圖直連清單（已自動排除 100x100 / 150x150 縮圖）
PRODUCT_IMAGES = [
    "https://drive.google.com/uc?export=view&id=1CJFvzI9QGJ2EQ-gQXrjaSaiVwKO5F415",  # 舒棉衣背面.png
    "https://drive.google.com/uc?export=view&id=1RaB0De8Ukb8mFm3yjBLzcz3VoLKgxXSS",  # 發熱衣-1.png
    "https://drive.google.com/uc?export=view&id=1nsx3f-hN0OZUB_xo_OlurTMD9s4wwcUN",  # 遠紅外線檢測報告.jpg
]

ANGLES = [
    "晚上蓋厚被子還是手腳冰冷，直接把遠紅外線熱感衣當暖睡衣穿，不靠厚重堆疊也能一夜好眠",
    "台灣早晚溫差大，早上出門防寒、進辦公室脫外套依然輕薄俐落不臃腫",
    "一件抵兩件：白天是隱形發熱打底衣，晚上直接當居家放鬆睡眠衣",
    "台灣製造、男女同款，幫另一半或怕冷的家人長輩一起準備，親膚無負擔"
]


# ================= 2. 免費 Gemini API 自動寫高轉換文案 =================
def generate_promo_copy() -> str:
    angle = random.choice(ANGLES)
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
    models = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.0-flash"]
    last_err = None

    for model in models:
        print(f"⏳ 正在呼叫 Gemini ({model})...", flush=True)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            resp = requests.post(
                url,
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=20
            ).json()
        except Exception as e:
            print(f"⚠️ {model} 連線異常：{e}", flush=True)
            last_err = e
            continue

        if "candidates" in resp:
            print(f"✅ 文案生成成功（{model}）", flush=True)
            return resp["candidates"][0]["content"]["parts"][0]["text"].strip()
        last_err = resp
        print(f"⚠️ {model} 略過：{resp.get('error', {}).get('message', resp)}", flush=True)

    raise RuntimeError(f"❌ Gemini API 呼叫失敗：{last_err}")


# ================= 3. 等待 Threads 圖片處理完成 =================
def wait_threads_container(creation_id: str, max_wait: int = 35):
    status_url = f"https://graph.threads.net/v1.0/{creation_id}"
    for sec in range(0, max_wait, 3):
        time.sleep(3)
        res = requests.get(
            status_url,
            params={"fields": "status,error_message", "access_token": THREADS_ACCESS_TOKEN},
            timeout=15
        ).json()
        status = res.get("status")
        print(f"⏳ Threads 圖片處理狀態 ({sec + 3}s)：{status}", flush=True)
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise RuntimeError(f"❌ Threads 處理圖片失敗：{res}")
    raise RuntimeError("❌ Threads 處理圖片超過 35 秒未完成")


# ================= 4. 自動發布到 Threads =================
def post_to_threads(text: str, image_url: str):
    print(f"⏳ 正在建立 Threads 圖文容器：{image_url}", flush=True)
    create_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
    payload = {
        "media_type": "IMAGE",
        "image_url": image_url,
        "text": text,
        "access_token": THREADS_ACCESS_TOKEN
    }

    create_res = requests.post(create_url, data=payload, timeout=20).json()
    creation_id = create_res.get("id")
    if not creation_id:
        raise RuntimeError(f"❌ Threads 建立圖文失敗：{create_res}")

    wait_threads_container(creation_id, max_wait=35)

    print("⏳ 正在正式發布到 Threads...", flush=True)
    pub_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish"
    pub_res = requests.post(
        pub_url,
        data={"creation_id": creation_id, "access_token": THREADS_ACCESS_TOKEN},
        timeout=20
    ).json()
    if "id" not in pub_res:
        raise RuntimeError(f"❌ Threads 發布失敗：{pub_res}")
    print(f"✅ Threads 圖文自動發文成功：{pub_res}", flush=True)


# ================= 5. 同步發布圖文到 IG（選配） =================
def post_to_ig(caption: str, image_url: str):
    if not (IG_USER_ID and META_ACCESS_TOKEN and image_url):
        return

    create_url = f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media"
    create_res = requests.post(
        create_url,
        data={"image_url": image_url, "caption": caption, "access_token": META_ACCESS_TOKEN},
        timeout=20
    ).json()

    creation_id = create_res.get("id")
    if not creation_id:
        raise RuntimeError(f"❌ IG 建立貼文失敗：{create_res}")

    time.sleep(6)

    pub_url = f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media_publish"
    pub_res = requests.post(
        pub_url,
        data={"creation_id": creation_id, "access_token": META_ACCESS_TOKEN},
        timeout=20
    ).json()
    print(f"✅ IG 自動發文成功：{pub_res}", flush=True)


if __name__ == "__main__":
    chosen_image = random.choice(PRODUCT_IMAGES)
    copy_text = generate_promo_copy()
    print(f"📝 本次 AI 生成文案：\n{copy_text}", flush=True)
    post_to_threads(copy_text, chosen_image)
    post_to_ig(copy_text, chosen_image)
