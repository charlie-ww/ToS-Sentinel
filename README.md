# 🛡️ ToS Sentinel - AI 服務條款掃雷 Agent

> **Cloud Computing and Data Analytics Final Project**
> Developed by 314511063 李兆翔 & 314511043 張恬嘉

## 📖 這是什麼？ (專案簡介)

簡單來說，這是一個**幫你讀落落長服務條款 (ToS)」的 AI 機器人**。

當你想註冊一個帳號（例如 OpenAI 或 LINE），但懶得看幾萬字的法律條款時，通常會直接按 "I Agree"。但你可能不知道，你的某些用途其實已經違反了條款，隨時會被封鎖帳號。

**ToS Sentinel 的運作方式：**

1.  給它一個網址（例如 OpenAI 條款）。
2.  告訴它**你想做什麼**（例如：「我想寫爬蟲抓你們的資料」或「我想單純聊天」）。
3.  AI 會自動爬取網頁、閱讀條款，並告訴你：**「這樣做會不會死（被 Ban）」**，以及風險在哪裡。

---

## 🛠️ 技術架構 (Tech Stack)

本專案採用微服務架構 (Microservices)，完全容器化 (Dockerized)，支援本地與雲端部署：

* **Frontend**: Streamlit (Python) - 提供直覺的互動介面與視覺化圖表。
* **Backend**: FastAPI (Async Python) - 處理核心邏輯與非同步任務。
* **Crawling Engine**: Playwright - 具備隱形模式 (Stealth Mode) 的瀏覽器自動化，可繞過 Cloudflare 防護。
* **RAG Engine**: ChromaDB + Gemini Embedding - 實現跨文件語意檢索 (Retrieval-Augmented Generation)。
* **LLM**: Google Gemini - 進行語意分析與風險評估。
* **Cloud Platform**: Google Cloud Run - 實現 Serverless 自動擴展部署。

---

## 🚀 快速開始：本地開發 (Local Installation)

如果你想在自己的電腦上跑，請依照以下步驟。

### 前置需求 (Prerequisites)
* 電腦已安裝 **Docker Desktop** (並已啟動)。
* 擁有一個 **Google Gemini API Key** (免費申請)。

### 第一步：設定環境變數 (.env)
這是最重要的一步！程式需要 API Key 才能運作。

1.  在專案**根目錄**下，建立一個新檔案，命名為 `.env`。
2.  複製以下內容貼進去，並填入你的 Key：

```ini
# .env file

# 1. Google Gemini API Key (必填)
# 請在此申請: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
GEMINI_API_KEY=你的_API_KEY_貼在這裡_不要有空格

# 2. 系統設定 (維持預設即可，不用改)
BACKEND_HOST=backend
CHROMA_HOST=chromadb
````

### 第二步：啟動服務 (Launch)

打開終端機 (Terminal / CMD)，進入專案資料夾，執行以下指令：

```bash
docker-compose up --build
```

  * **注意**：第一次執行需要下載瀏覽器核心與 Python 套件，可能會花 3-5 分鐘，請耐心等待。
  * 當你看到終端機出現 `Uvicorn running on http://0.0.0.0:8000` 或前端顯示 URL 時，代表啟動成功。

### 第三步：開始使用 (Usage)

1.  打開瀏覽器，前往：**[http://localhost:8501](https://www.google.com/search?q=http://localhost:8501)**
2.  開始輸入網址進行分析。

-----

## ☁️ 進階指南：部署至 Google Cloud (Deploy to GCP)

如果你想將此服務部署到雲端，讓其他人也能使用，請參考以下 Cloud Run 部署流程。

### 前置需求

1.  **Google Cloud 帳號** 與 **已啟用計費的專案**。
2.  **Google Cloud SDK** 已安裝並登入 (`gcloud auth login`)。

### 步驟 1：初始化專案環境

在終端機 (或 Google Cloud Shell) 執行：

```powershell
# 設定你的專案 ID
gcloud config set project [你的_PROJECT_ID]

# 啟用必要的 API (Cloud Run, Build, Artifact Registry)
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

### 步驟 2：部署 Backend (API 服務)

後端負責處理爬蟲與 AI 邏輯，需要較高的記憶體。

```powershell
# 部署 Backend（請將 your_api_key 替換為真實的 Gemini Key）
gcloud run deploy tos-sentinel-backend 
  --source ./backend 
  --region asia-east1 
  --memory 2Gi 
  --timeout 3600 
  --set-env-vars GEMINI_API_KEY=your_gemini_api_key 
  --allow-unauthenticated 
  --port 8000
```

**等待 3-5 分鐘，部署完成後，終端機顯示一組 `Service URL`，請複製下來（我們稱之為 `$BACKEND_URL`）。**

### 步驟 3：部署 Frontend (UI 介面)

前端需要知道後端的網址才能溝通。

```powershell
# 部署 Frontend (將 $BACKEND_URL 替換為步驟 2 拿到的網址)
gcloud run deploy tos-sentinel-frontend 
  --source ./frontend 
  --region asia-east1 
  --memory 1Gi 
  --set-env-vars BACKEND_URL=[https://你的-backend-網址.run.app](https://你的-backend-網址.run.app) 
  --allow-unauthenticated 
  --port 8080
```

### 步驟 4：訪問雲端應用

部署完成後，點擊終端機顯示的 Frontend URL，即可在網路上使用你的 ToS Sentinel！

-----

## 🛑 如何關閉 (Shutdown - Local)

要完整關閉本地服務並釋放資源，請在終端機按下 `Ctrl + C`，或者開一個新視窗執行：

```bash
docker-compose down
```

-----

## 💡 常見問題 (Troubleshooting)

**Q1: 為什麼第一次跑這麼久？**
A: 因為 Docker 需要下載 Chromium 瀏覽器核心和相關依賴，這是正常的。第二次啟動就會在 1 秒內完成。

**Q2: 跑出一堆 "Skipped (Too short)" 的 Log 是壞掉了嗎？**
A: 不一定。有些網站有強大的反爬蟲機制 (Cloudflare)，或者該連結只是跳轉頁。只要 Log 中有顯示 `✅ Saved XXX chars`，代表核心內容有抓到，RAG 依然能運作。

**Q3: 為什麼要用 RAG？單看一頁不行嗎？**
A: 現代法律條款通常四分五裂。主頁面只寫「請遵守規範」，但規範細節藏在「使用政策」或「隱私權條款」裡。開啟 RAG 後，Agent 會自動把這些關聯文件抓回來分析，避免遺漏關鍵風險。

-----

## 🎬 Demo 演示腳本 (Test Scenarios)

以下提供四組經典測試情境，分別展示本系統的不同核心能力（RAG 檢索、意圖判斷、風險區隔）。

### 情境 1 & 2：RAG 的威力 (The Power of RAG)

**展示目標**：比較開啟 RAG 前後，AI 能否抓到藏在關聯文件中的隱私條款。

  * **Target URL**: `https://terms2.line.me/official_account_terms_tw` (LINE 官方帳號條款)
  * **User Intent**:
    ```text
    我想創帳號跟別人聊天
    ```

**測試步驟：**

1.  **RAG Off**: 執行分析。
      * *預期結果*：可能只看到官方帳號的商業規範，資訊不全。
2.  **RAG On**: 開啟 Deep RAG 並再次執行。
      * *預期結果*：系統會自動抓取 **隱私權政策 (Privacy Policy)** 與 **通用服務條款**。報告應會新增關於「資料用於廣告」或「訊息內容審查」的隱私提示 (Low/Medium Risk)，證明 AI 讀到了額外文件。

### 情境 3：良民 vs. 惡意使用者 (Good vs. Bad Actor)

**展示目標**：展示 AI 如何根據使用者的「意圖」動態改變評分，而非死板地背誦法條。

  * **Target URL**: `https://discord.com/terms`

**測試 A (良民)**：

  * **User Intent**:
    ```text
    我想在DC認識新朋友
    ```
  * *觀察重點*：即使 ToS 裡有很多禁止事項，但因為意圖良善，Risk Score 應為 **Medium** 以下。

**測試 B (惡意)**：

  * **User Intent**:
    ```text
    我想在DC朋友群發表反社會言論
    ```
  * *觀察重點*：這直接違反了 Discord 的社群守則 (Community Guidelines)。Risk Score 應飆升至 **High (75分以上)**，並引用禁止仇恨言論或暴力內容的條款。

### 情境 4：灰色地帶與帳號安全 (Account Security)

**展示目標**：測試 AI 對於「帳號共用」與「規避付費」類型的風險判斷。

  * **Target URL**: `https://policies.google.com/terms?hl=en-US`
  * **User Intent**:
    ```text
    我想創個新帳號透過google帳號共享GPTplus
    ```
  * *觀察重點*：
      * 雖然 Google 條款很長，但 AI 應能識別出「帳號密碼共用」或「安全性」相關的條款。
      * 通常這類行為違反了 "Account Security" 或 "Responsible Use" 政策，預期會得到 **Medium** 或 **High** 的風險評級，因為這涉及帳號安全風險與潛在的濫用。

<!-- end list -->
