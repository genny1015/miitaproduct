import os
import requests


def check_secrets():
    required = ["GEMINI_API_KEY", "THREADS_USER_ID", "THREADS_ACCESS_TOKEN"]
    missing = []
    for k in required:
        val = os.environ.get(k, "")
        if not val.strip():
            missing.append(k)
        elif val != val.strip():
            print(f"⚠️ {k} 前後有空白或換行，建議重新貼上避免隱形字元。")
        else:
            print(f"✅ {k} 已設定")
    if missing:
        raise RuntimeError(f"❌ 缺少必要 Secrets：{', '.join(missing)}")


def check_gemini():
    key = os.environ["GEMINI_API_KEY"].strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
    res = requests.get(url, timeout=15)
    data = res.json()
    if res.status_code != 200 or "models" not in data:
        raise RuntimeError(f"❌ Gemini 金鑰或連線異常：{data}")

    flash_models = [
        m.get("name", "").replace("models/", "")
        for m in data["models"]
        if "generateContent" in m.get("supportedGenerationMethods", [])
        and "flash" in m.get("name", "")
    ]
    print(f"✅ Gemini 連線正常，可用 Flash 模型：{flash_models[:5]}")


def check_threads():
    user_id = os.environ["THREADS_USER_ID"].strip()
    token = os.environ["THREADS_ACCESS_TOKEN"].strip()
    url = f"https://graph.threads.net/v1.0/me?fields=id,username&access_token={token}"
    res = requests.get(url, timeout=15)
    data = res.json()
    if res.status_code != 200 or "id" not in data:
        raise RuntimeError(f"❌ Threads Token 或 User ID 異常：{data}")

    fetched_id = str(data["id"])
    if fetched_id != user_id:
        print(f"⚠️ 提醒：Secret 的 THREADS_USER_ID ({user_id}) 與 Token 對應帳號 ID ({fetched_id}) 不一致！")
    else:
        print(f"✅ Threads 驗證通過：@{data.get('username')} (ID: {fetched_id})")


if __name__ == "__main__":
    print("🔍 開始檢查 MiiTA 自動發文環境...")
    check_secrets()
    check_gemini()
    check_threads()
    print("🎉 全部檢查通過，可以安心執行 auto_promo.py！")
