import os
import random
import time
import requests

# ================= 1. 環境變數與商品設定 =================
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"].strip()
THREADS_USER_ID = os.environ["THREADS_USER_ID"].strip()
THREADS_ACCESS_TOKEN = os.environ["THREADS_ACCESS_TOKEN"].strip()

# 若要同步發 IG，請在 GitHub Secrets 填入以下兩個值（沒填則只自動發 Threads）
IG_USER_ID = os.environ.get("IG_USER_ID", "").strip()
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", "").strip()

PRODUCT_URL = "https://miitamed.com/shop/heartwear/?utm_source=social_auto&utm_medium=ai_post&utm_campaign=heartwear"

# 官網商品真實圖片清單（每次發文自動隨機輪播）
PRODUCT_IMAGES = [
    "https://miitamed.com/wp-content/uploads/%E8%88%92%E6%A3%89%E8%A1%A3%E6%AD%A3%E9%9D%A22-scaled.jpg",
    "https://miitamed.com/wp-content/uploads/%E8%88%92%E6%A3%89%E8%A1%A3%E8%83%8C%E9%9D%A2.png",
    "https://miitamed.com/wp-content/uploads/%E7%99%BC%E7%86%B1%E8%A1%A3-1.png",
]

ANGLES = [
    "晚上蓋厚被子還是手腳冰冷，直接把遠紅外線熱感衣當暖睡衣穿，不靠厚重堆疊也能一夜好眠",
    "台灣早晚溫差大，早上出門防寒、進辦公室脫外套依然輕薄俐落不臃腫",
    "一件抵兩件：白天是隱形發熱打底衣，晚上直接當居家放鬆睡眠衣",
    "台灣製造、男女同款，幫另一半或怕冷的家人長輩一起準備，親膚無負擔"
]


# ================= 2. 免費 Gemini API 自動寫高轉換文案 =================
def get_available_models() -> list[str]:
    candidates = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.0-flash"]
    try:
        list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
        data = requests.get(list_url, timeout=15).json()
        for m in data.get("models", []):
            name = m.get("name", "").replace("models/", "")
            methods = m.get("supportedGenerationMethods", [])
            if "generateContent" in methods and "flash" in name and "lite" not in name:
                if name not in candidates:
                    candidates.append(name)
    except Exception as e:
        print(f"⚠️ 取得模型清單略過：{e}")
    return candidates


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
    last_err = None
    for model in get_available_models():
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        resp = requests.post(url, json={
            "contents": [{"parts": [{"text": prompt}]}]
        }).json()

        if "candidates" in resp:
            print(f"✅ 使用模型：{model}")
            return resp["candidates"][0]["content"]["parts"][0]["text"].strip()
        last_err = resp
        print(f"⚠️ 模型 {model} 略過：{resp.get('error', {}).get('message', resp)}")

    raise RuntimeError(f"❌ Gemini API 呼叫失敗，詳細原因：{last_err}")


# ================= 3. 自動發布到 Threads（有圖發圖文、無圖發純文字） =================
def post_to_threads(text: str, image_url: str = ""):
    create_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
    payload = {
        "text": text,
        "access_token": THREADS_ACCESS_TOKEN
    }
    if image_url:
        payload["media_type"] = "IMAGE"
        payload["image_url"] = image_url
    else:
        payload["media_type"] = "TEXT"

    create_res = requests.post(create_url, data=payload).json()
    creation_id = create_res.get("id")
    if not creation_id:
        raise RuntimeError(f"❌ Threads 建立貼文失敗：{create_res}")

    time.sleep(6 if image_url else 3)

    pub_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish"
    pub_res = requests.post(pub_url, data={
        "creation_id": creation_id,
        "access_token": THREADS_ACCESS_TOKEN
    }).json()
    print(f"✅ Threads 自動發文成功（{'圖文' if image_url else '純文字'}）：", pub_res)


# ================= 4. 同步發布圖文到 IG（需設定 IG Secrets 且有圖片網址） =================
def post_to_ig(caption: str, image_url: str):
    if not (IG_USER_ID and META_ACCESS_TOKEN and image_url):
        print("ℹ️ 尚未設定 IG Secrets，略過 IG 發布。")
        return

    create_url = f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media"
    create_res = requests.post(create_url, data={
        "image_url": image_url,
        "caption": caption,
        "access_token": META_ACCESS_TOKEN
    }).json()

    creation_id = create_res.get("id")
    if not creation_id:
        raise RuntimeError(f"❌ IG 建立貼文失敗：{create_res}")

    time.sleep(6)

    pub_url = f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media_publish"
    pub_res = requests.post(pub_url, data={
        "creation_id": creation_id,
        "access_token": META_ACCESS_TOKEN
    }).json()
    print("✅ IG 自動發文成功：", pub_res)


if __name__ == "__main__":
    valid_images = [img.strip() for img in PRODUCT_IMAGES if img.strip()]
    chosen_image = random.choice(valid_images) if valid_images else ""
    if chosen_image:
        print("🖼️ 本次隨機選用商品圖：", chosen_image)

    copy_text = generate_promo_copy()
    print("📝 本次 AI 生成文案：\n", copy_text)
    post_to_threads(copy_text, chosen_image)
    post_to_ig(copy_text, chosen_image)
