import os
import random
import time
import requests

# ================= 1. 環境變數與商品設定 =================
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"].strip()
THREADS_USER_ID = os.environ["THREADS_USER_ID"].strip()
THREADS_ACCESS_TOKEN = os.environ["THREADS_ACCESS_TOKEN"].strip()

# IG 雙平台同步設定（在 GitHub Secrets 填入這兩個值就會自動同步發 @miita.tw）
IG_USER_ID = os.environ.get("IG_USER_ID", "").strip()
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", "").strip()

PRODUCT_URL = "https://miitamed.com/shop/heartwear/?utm_source=social_auto&utm_medium=ai_post&utm_campaign=heartwear"

# Google 雲端硬碟高畫質原圖直連清單
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

FALLBACK_COPIES = [
    f"晚上蓋厚被子還是手腳冰冷到睡不著嗎？試試把「MiiTA 遠紅外線熱感衣」直接當暖睡衣穿！台灣製造遠紅外線機能布料，溫和蓄熱、透氣不悶汗，白天當百搭發熱打底、晚上直接穿著睡，一件抵兩件超實穿。男女同款，現在就替自己與家人準備 👉 {PRODUCT_URL} #MiiTA遠紅外線熱感衣 #台灣製造",
    f"台灣早晚溫差大，穿太厚進室內又悶熱？這件「MiiTA 遠紅外線熱感衣」輕薄親膚不臃腫，靠遠紅外線溫和蓄熱保暖，白天當打底衣俐落有型，回家直接當居家睡眠衣超放鬆！男女同款台灣製造，立即逛逛 👉 {PRODUCT_URL} #MiiTA遠紅外線熱感衣 #暖睡衣推薦"
]


# ================= 2. 取得可用 Flash 模型清單 =================
def get_flash_models() -> list[str]:
    models = ["gemini-3.8-flash", "gemini-3.5-flash"]
    try:
        r = requests.get(
            f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}",
            timeout=15
        ).json()
        for m in r.get("models", []):
            name = m.get("name", "").replace("models/", "")
            methods = m.get("supportedGenerationMethods", [])
            if "generateContent" in methods and "flash" in name and "lite" not in name and "tts" not in name and "image" not in name:
                if name not in models:
                    models.append(name)
    except Exception as e:
        print(f"⚠️ 取得模型清單略過：{e}", flush=True)
    return models


# ================= 3. 免費 Gemini API 自動寫高轉換文案 =================
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
    for model in get_flash_models():
        print(f"⏳ 正在呼叫 Gemini ({model})...", flush=True)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"thinkingConfig": {"thinkingBudget": 0}}
        }
        try:
            resp = requests.post(url, json=payload, timeout=60).json()
        except Exception as e:
            print(f"⚠️ {model} 連線異常：{e}", flush=True)
            continue

        if "candidates" in resp:
            print(f"✅ 文案生成成功（{model}）", flush=True)
            return resp["candidates"][0]["content"]["parts"][0]["text"].strip()
        print(f"⚠️ {model} 略過：{resp.get('error', {}).get('message', resp)}", flush=True)

    print("ℹ️ Gemini 暫時忙碌，啟用高轉換備用文案確保準時發文。", flush=True)
    return random.choice(FALLBACK_COPIES)


# ================= 4. 自動發布到 Threads =================
def wait_threads_container(creation_id: str, max_wait: int = 40):
    status_url = f"https://graph.threads.net/v1.0/{creation_id}"
    for sec in range(0, max_wait, 4):
        time.sleep(4)
        res = requests.get(
            status_url,
            params={"fields": "status,error_message", "access_token": THREADS_ACCESS_TOKEN},
            timeout=20
        ).json()
        status = res.get("status")
        print(f"⏳ Threads 圖片處理狀態 ({sec + 4}s)：{status}", flush=True)
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise RuntimeError(f"❌ Threads 處理圖片失敗：{res}")
    raise RuntimeError("❌ Threads 處理圖片超過 40 秒未完成")


def post_to_threads(text: str, image_url: str):
    print(f"⏳ [Threads] 正在建立圖文容器：{image_url}", flush=True)
    create_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
    create_res = requests.post(
        create_url,
        data={
            "media_type": "IMAGE",
            "image_url": image_url,
            "text": text,
            "access_token": THREADS_ACCESS_TOKEN
        },
        timeout=30
    ).json()

    creation_id = create_res.get("id")
    if not creation_id:
        raise RuntimeError(f"❌ [Threads] 建立圖文失敗：{create_res}")

    wait_threads_container(creation_id, max_wait=40)

    pub_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish"
    pub_res = requests.post(
        pub_url,
        data={"creation_id": creation_id, "access_token": THREADS_ACCESS_TOKEN},
        timeout=30
    ).json()
    if "id" not in pub_res:
        raise RuntimeError(f"❌ [Threads] 發布失敗：{pub_res}")
    print(f"✅ [Threads] 圖文自動發文成功：{pub_res}", flush=True)


# ================= 5. 同步發布圖文到 IG（@miita.tw） =================
def wait_ig_container(creation_id: str, max_wait: int = 40):
    status_url = f"https://graph.facebook.com/v21.0/{creation_id}"
    for sec in range(0, max_wait, 4):
        time.sleep(4)
        res = requests.get(
            status_url,
            params={"fields": "status_code,status", "access_token": META_ACCESS_TOKEN},
            timeout=20
        ).json()
        status = res.get("status_code") or res.get("status")
        print(f"⏳ IG 圖片處理狀態 ({sec + 4}s)：{status}", flush=True)
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise RuntimeError(f"❌ [IG] 處理圖片失敗：{res}")
    raise RuntimeError("❌ [IG] 處理圖片超過 40 秒未完成")


def post_to_ig(caption: str, image_url: str):
    if not (IG_USER_ID and META_ACCESS_TOKEN):
        print("ℹ️ 尚未設定 IG_USER_ID 或 META_ACCESS_TOKEN，本次略過 IG 發布。", flush=True)
        return

    print(f"⏳ [IG @miita.tw] 正在建立圖文容器：{image_url}", flush=True)
    create_url = f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media"
    create_res = requests.post(
        create_url,
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": META_ACCESS_TOKEN
        },
        timeout=30
    ).json()

    creation_id = create_res.get("id")
    if not creation_id:
        raise RuntimeError(f"❌ [IG] 建立貼文失敗：{create_res}")

    wait_ig_container(creation_id, max_wait=40)

    pub_url = f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media_publish"
    pub_res = requests.post(
        pub_url,
        data={"creation_id": creation_id, "access_token": META_ACCESS_TOKEN},
        timeout=30
    ).json()
    if "id" not in pub_res:
        raise RuntimeError(f"❌ [IG] 發布失敗：{pub_res}")
    print(f"✅ [IG @miita.tw] 圖文自動發文成功：{pub_res}", flush=True)


# ================= 6. 雙平台主流程（互不干擾防呆） =================
if __name__ == "__main__":
    chosen_image = random.choice(PRODUCT_IMAGES)
    copy_text = generate_promo_copy()
    print(f"📝 本次生成文案：\n{copy_text}", flush=True)

    errors = []

    # 1. 發布到 Threads（保留完整可點擊商品網址）
    try:
        post_to_threads(copy_text, chosen_image)
    except Exception as e:
        print(e, flush=True)
        errors.append(str(e))

    # 2. 同步發布到 IG（@miita.tw，把無法點擊的長網址替換為引導點擊主頁連結）
    try:
        ig_caption = copy_text.replace(PRODUCT_URL, "點擊 @miita.tw 主頁連結立即逛逛 👆")
        post_to_ig(ig_caption, chosen_image)
    except Exception as e:
        print(e, flush=True)
        errors.append(str(e))

    if errors:
        raise RuntimeError(" | ".join(errors))
