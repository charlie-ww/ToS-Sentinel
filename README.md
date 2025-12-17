# 🛡️ ToS Sentinel - AI 服務條款掃雷 Agent (雲端部署版本)

> **Cloud Computing and Data Analytics Final Project**  
> Developed by 314511043 張恬嘉

## 📖 專案簡介

**ToS Sentinel** 是一個基於 AI 的服務條款風險分析工具，能夠自動爬取、閱讀網站的服務條款（Terms of Service），並根據使用者意圖評估潛在風險。

### 核心功能
- 🕷️ **智能網頁爬蟲** - 使用 Playwright 自動爬取服務條款及相關法律文件
- 🧠 **AI 風險分析** - 透過 Google Gemini AI 進行語意理解與風險評估
- 🔍 **RAG 檢索增強** - 使用 ChromaDB 向量資料庫實現跨文件檢索
- 📊 **視覺化報告** - Streamlit 互動介面呈現風險評分與證據引用
- ☁️ **雲端部署** - 完全部署於 Google Cloud Run，支援自動擴展

### 使用場景
當你想使用某個線上服務（如 OpenAI、Discord、LINE）但不確定你的使用方式是否違反條款時：
1. 輸入服務條款 URL
2. 描述你的使用意圖（例如：「我想用爬蟲抓資料」）
3. AI 自動分析並告訴你風險等級和潛在問題

---

## 🛠️ 技術架構

### 雲端架構圖
```
Internet
   │
   ├─► Frontend (Cloud Run)
   │    └─► Streamlit UI (8080)
   │         │
   │         └─► Backend (Cloud Run)
   │              └─► FastAPI + Playwright (8000)
   │                   │
   │                   ├─► Google Gemini API (LLM & Embedding)
   │                   └─► ChromaDB (In-Memory Vector DB)
```

### 技術棧
| 層級 | 技術 | 用途 |
|------|------|------|
| **雲端平台** | Google Cloud Run | 無伺服器容器部署 |
| **前端** | Streamlit | 互動式 Web UI |
| **後端** | FastAPI | RESTful API 服務 |
| **爬蟲** | Playwright | 無頭瀏覽器自動化 |
| **AI 模型** | Google Gemini | 語意分析與生成 |
| **向量資料庫** | ChromaDB | RAG 檢索引擎 |
| **容器化** | Docker | 服務封裝 |

---

## ☁️ 雲端部署指南

### 前置需求
1. **Google Cloud 帳號** - [註冊連結](https://cloud.google.com/)
2. **已啟用計費的 GCP 專案(可免費使用)**
3. **Google Cloud SDK** - [安裝指南](https://cloud.google.com/sdk/docs/install)
4. **Gemini API Key** - [申請連結](https://aistudio.google.com/app/apikey)

### 快速部署（5 分鐘）

#### 步驟 1：初始化並「新增」GCP 專案（在 Google Cloud Shell 執行）
```powershell
# 1) 登入 Google Cloud
gcloud auth login

# 2) 建立專案
gcloud projects create $PROJECT_ID

# 3) 切換到新專案
gcloud config set project $PROJECT_ID

# 4) 啟用必要的 API
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

#### 步驟 2：部署 Backend
```powershell
# 進入專案目錄
cd ToS-Sentinel_cloud

# 部署 Backend（替換為你的 API Key）
gcloud run deploy tos-sentinel-backend `
  --source ./backend `
  --region asia-east1 `
  --memory 2Gi `
  --timeout 3600 `
  --set-env-vars GEMINI_API_KEY=your_gemini_api_key `
  --allow-unauthenticated `
  --port 8000
```

**等待 3-5 分鐘，完成後會顯示 Backend URL**

#### 步驟 3：部署 Frontend
```powershell
# 部署 Frontend
gcloud run deploy tos-sentinel-frontend `
  --source ./frontend `
  --region asia-east1 `
  --memory 1Gi `
  --timeout 3600 `
  --set-env-vars BACKEND_URL=$BACKEND_URL `
  --allow-unauthenticated `
  --port 8080
```
**等待 3-5 分鐘，完成後會顯示 Frontend URL**
#### 步驟 4：訪問應用
```powershell
# 在瀏覽器中開啟
$FRONTEND_URL
```

---

## 🎯 使用方法

### 基本操作流程
1. **開啟 Frontend URL** - 訪問部署完成後的雲端網址
2. **選擇 AI 模型** - 左側選單選擇 Gemini 模型（建議：gemini-2.5-flash）
3. **啟用 Deep RAG** - 開啟以分析關聯文件（隱私政策、使用指南等）
4. **輸入目標 URL** - 貼上要分析的服務條款網址
5. **描述使用意圖** - 說明你想做什麼（例如：「我想用爬蟲抓資料」）
6. **點擊 Analyze Risk** - 等待 AI 分析（約 30-60 秒）
7. **查看結果** - 檢視風險評分、違規項目與建議

### 測試案例

#### 案例 1：低風險場景
- **URL**: `https://terms2.line.me/official_account_terms_tw`
- **意圖**: 我想創帳號跟別人聊天
- **預期結果**: Risk Score < 35，無重大違規

#### 案例 2：高風險場景
- **URL**: `https://openai.com/policies/terms-of-use`
- **意圖**: 我想用爬蟲大量抓取 OpenAI 的資料
- **預期結果**: Risk Score > 75，明確違反自動化使用條款

#### 案例 3：RAG 對比測試
- **URL**: `https://discord.com/terms`
- **意圖**: 我想在 Discord 發表反社會言論
- **測試方式**: 先關閉 RAG 再開啟 RAG，比較結果差異
- **預期結果**: 開啟 RAG 後會檢索到 Community Guidelines，風險評分更高

---

## 📊 雲端運算特性展示

本專案完整展示了以下雲端運算核心概念：

### 1. 無伺服器架構 (Serverless Computing)
- ✅ 無需管理伺服器，專注於應用邏輯
- ✅ 自動處理基礎設施維護與更新
- ✅ 零停機時間部署

### 2. 容器化與微服務 (Containerization & Microservices)
- ✅ Frontend/Backend 獨立部署
- ✅ Docker 容器封裝依賴環境
- ✅ 服務間透過 RESTful API 通訊

### 3. 彈性擴展 (Auto-scaling)
- ✅ 根據流量自動增減實例
- ✅ 從 0 擴展到 N（請求時自動喚醒）
- ✅ 無流量時自動縮減至 0

### 4. 按使用量計費 (Pay-as-you-go)
- ✅ 沒有請求時不收費
- ✅ 只為實際使用的 CPU/Memory 付費
- ✅ 免費額度充足（200 萬次請求/月）

### 5. 高可用性 (High Availability)
- ✅ 自動健康檢查與故障恢復
- ✅ 多區域負載均衡
- ✅ 99.95% SLA 保證

### 6. 環境隔離 (Environment Isolation)
- ✅ 開發環境（本地 Docker）與生產環境（Cloud Run）分離
- ✅ 環境變數動態注入
- ✅ 敏感資訊透過 Secret Manager 管理

---

## 🔍 監控與管理

### 查看服務狀態
```powershell
# Backend 狀態
gcloud run services describe tos-sentinel-backend --region asia-east1

# Frontend 狀態
gcloud run services describe tos-sentinel-frontend --region asia-east1
```

### 查看即時日誌
```powershell
# Backend 日誌
gcloud run logs read tos-sentinel-backend --region asia-east1 --limit 50

# Frontend 日誌
gcloud run logs read tos-sentinel-frontend --region asia-east1 --limit 50

# 即時串流日誌
gcloud run logs tail tos-sentinel-backend --region asia-east1
```

### 更新服務
```powershell
# 修改代碼後重新部署 Backend
gcloud run deploy tos-sentinel-backend --source ./backend --region asia-east1

# 修改代碼後重新部署 Frontend
gcloud run deploy tos-sentinel-frontend --source ./frontend --region asia-east1
```

### 更新環境變數
```powershell
# 更新 Backend API Key
gcloud run services update tos-sentinel-backend `
  --region asia-east1 `
  --update-env-vars GEMINI_API_KEY=new_api_key

# 更新 Frontend Backend URL
gcloud run services update tos-sentinel-frontend `
  --region asia-east1 `
  --update-env-vars BACKEND_URL=new_backend_url
```

### 刪除服務
```powershell
# 刪除 Frontend
gcloud run services delete tos-sentinel-frontend --region asia-east1

# 刪除 Backend
gcloud run services delete tos-sentinel-backend --region asia-east1
```

---

## 💰 成本估算

### Google Cloud Run 免費額度（每月）
- 200 萬次請求
- 36 萬 GB-秒記憶體
- 18 萬 vCPU-秒 CPU
- 1 GB 網路流出（北美）

### 實際使用成本預估
| 使用量 | 每月請求數 | 預估成本 |
|--------|-----------|---------|
| 輕度使用 | < 100 次分析 | **$0 (免費額度內)** |
| 中度使用 | 500 次分析 | **$1-3 USD** |
| 重度使用 | 2000 次分析 | **$5-10 USD** |

**註**: 每次分析約消耗 2-3 個請求（UI 載入 + API 呼叫）

### Gemini API 成本
- **Gemini 2.5 Flash**: $0.075 / 1M tokens (Input), $0.30 / 1M tokens (Output)
- **每次分析約消耗**: 20K-50K tokens
- **預估成本**: 每次分析 < $0.01 USD

---

## 📚 API 文檔

### Backend Endpoints

#### `GET /models`
取得可用的 Gemini 模型列表

**Response:**
```json
{
  "models": [
    "gemini-2.5-flash",
    "gemini-2.0-flash-exp",
    "gemini-1.5-pro-latest"
  ]
}
```

#### `POST /analyze`
分析服務條款風險

**Request Body:**
```json
{
  "url": "https://example.com/terms",
  "intent": "我想用爬蟲抓資料",
  "model_name": "gemini-2.5-flash",
  "enable_rag": true
}
```

**Response:** Server-Sent Events (SSE) 串流
```json
{"type": "log", "msg": "🕸️ Starting scraper..."}
{"type": "log", "msg": "✅ Main page captured (15234 chars)"}
{"type": "result", "data": {...}}
```

---

## 🔒 安全性最佳實踐

### 1. API Key 管理
- ❌ 不要將 API Key 硬編碼在代碼中
- ❌ 不要將 API Key 提交到 Git
- ✅ 使用環境變數注入
- ✅ 考慮使用 Google Secret Manager

### 2. 網路安全
- ✅ 所有服務預設使用 HTTPS
- ✅ Cloud Run 提供自動 SSL 憑證
- ✅ 考慮添加 Identity-Aware Proxy (IAP) 進行身份驗證

### 3. 成本控制
```powershell
# 設定最大實例數（避免意外高額費用）
gcloud run services update tos-sentinel-backend `
  --region asia-east1 `
  --max-instances 10
```

---

## 🐛 常見問題排查

### 問題 1: Backend 啟動失敗
**錯誤訊息**: `Container failed to start`

**解決方法**:
```powershell
# 查看詳細日誌
gcloud run logs read tos-sentinel-backend --region asia-east1 --limit 100

# 檢查是否是 API Key 問題
gcloud run services describe tos-sentinel-backend --region asia-east1 --format="value(spec.template.spec.containers[0].env)"
```

### 問題 2: Frontend 無法連接 Backend
**錯誤訊息**: `Connection refused` 或 `CORS error`

**解決方法**:
```powershell
# 確認 Backend URL 是否正確
$BACKEND_URL = (gcloud run services describe tos-sentinel-backend --region asia-east1 --format='value(status.url)')
Write-Host $BACKEND_URL

# 更新 Frontend 環境變數
gcloud run services update tos-sentinel-frontend `
  --region asia-east1 `
  --update-env-vars BACKEND_URL=$BACKEND_URL
```

### 問題 3: 模型列表為空或錯誤
**錯誤訊息**: `404 models/gemini-xxx is not found`

**解決方法**: Gemini API 模型名稱可能已更新，修改 `backend/main.py`:
```python
# 使用最新的模型名稱
return {"models": ["gemini-2.5-flash", "gemini-2.0-flash-exp"]}
```

### 問題 4: 部署超時
**錯誤訊息**: `Build timeout`

**解決方法**:
```powershell
# 增加建置超時時間
gcloud config set builds/timeout 1200  # 20 分鐘

# 重新部署
gcloud run deploy tos-sentinel-backend --source ./backend --region asia-east1
```

---

## 📂 專案結構

```
ToS-Sentinel_cloud/
├── README.md                    # 本文檔
├── .dockerignore                # Docker 建置忽略檔案
├── .gcloudignore                # GCP 上傳忽略檔案
├── backend/                     # 後端服務
│   ├── main.py                  # FastAPI 主程式
│   ├── Dockerfile               # 後端容器配置
│   └── requirements.txt         # Python 依賴
└── frontend/                    # 前端服務
    ├── app.py                   # Streamlit 主程式
    ├── Dockerfile               # 前端容器配置
    └── requirements.txt         # Python 依賴
```

---

## 🎓 課程報告重點

### 展示的雲端運算核心能力
1. ✅ **Infrastructure as Code** - Dockerfile 定義基礎設施
2. ✅ **CI/CD Pipeline** - 透過 Cloud Build 自動建置部署
3. ✅ **Containerization** - Docker 容器化應用
4. ✅ **Microservices Architecture** - Frontend/Backend 解耦
5. ✅ **API Gateway Pattern** - Backend 作為統一入口
6. ✅ **Serverless Computing** - Cloud Run 無伺服器部署
7. ✅ **Auto-scaling** - 根據負載自動擴展
8. ✅ **Observability** - Cloud Logging 集中日誌
9. ✅ **Security Best Practices** - 環境變數管理敏感資訊
10. ✅ **Cost Optimization** - 按使用量付費，無流量時零成本

### 技術挑戰與解決方案
| 挑戰 | 解決方案 |
|------|---------|
| **Playwright 在容器中運行** | 使用官方 Playwright Docker Image |
| **ChromaDB 持久化** | Cloud Run 不支持持久化，改用 In-Memory 模式 |
| **CORS 跨域問題** | FastAPI 添加 CORS middleware |
| **Streamlit 在 Cloud Run 的端口問題** | 配置 `config.toml` 監聽 8080 |
| **環境變數安全** | 使用 `--set-env-vars` 注入，避免硬編碼 |

---

## 📞 聯絡資訊

**開發者**: 張恬嘉  
**學號**: 314511043  
**課程**: Cloud Computing and Data Analytics  
**學期**: 2025 Fall  
**專案連結**: GitHub Repository  
**線上展示**: Frontend URL

---

## 📄 授權與致謝

### 使用的第三方服務
- **Google Gemini API** - [Terms of Service](https://ai.google.dev/terms)
- **Google Cloud Run** - [Service Terms](https://cloud.google.com/terms)
- **Playwright** - [Apache License 2.0](https://github.com/microsoft/playwright/blob/main/LICENSE)
- **Streamlit** - [Apache License 2.0](https://github.com/streamlit/streamlit/blob/develop/LICENSE)
- **FastAPI** - [MIT License](https://github.com/tiangolo/fastapi/blob/master/LICENSE)

### 致謝
- 感謝課程教授的指導
- 感謝 AI 工具在開發過程中的協助
- 感謝開源社群提供的優秀工具

---

## 🔗 相關資源

- [Google Cloud Run 文檔](https://cloud.google.com/run/docs)
- [Google Gemini API 文檔](https://ai.google.dev/docs)
- [Playwright 文檔](https://playwright.dev/)
- [Streamlit 文檔](https://docs.streamlit.io/)
- [FastAPI 文檔](https://fastapi.tiangolo.com/)
- [Docker 文檔](https://docs.docker.com/)

---

**最後更新**: 2025 年 12 月 16 日

  * **User Intent**:
    ```text
    我想在DC朋友群發表反社會言論
    ```
  * *觀察重點*：這直接違反了 Discord 的社群守則 (Community Guidelines)。Risk Score 應飆升至 **High (75分以上)**，並引用禁止仇恨言論或暴力內容的條款。

-----

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
