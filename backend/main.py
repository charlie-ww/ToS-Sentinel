import os
import json
import re
import uuid
import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import google.generativeai as genai
from playwright.sync_api import sync_playwright
import chromadb

app = FastAPI()

GENAI_KEY = os.getenv("GEMINI_API_KEY")
CHROMA_HOST = os.getenv("CHROMA_HOST", "chromadb")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))

if not GENAI_KEY:
    raise RuntimeError("Gemini API Key is missing!")

genai.configure(api_key=GENAI_KEY)
'''
try:
    chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    print(f"✅ Connected to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}")
except Exception as e:
    print(f"⚠️ ChromaDB connection failed: {e}")
    chroma_client = None
'''
try:
# 優先嘗試連到外部/遠端 Chroma HTTP 服務（若有）
    chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    print(f"✅ Connected to ChromaDB (HTTP) at {CHROMA_HOST}:{CHROMA_PORT}")
except Exception as e_http:
    print(f"⚠️ ChromaDB HTTP connection failed: {e_http} — falling back to local client")
try:
# 在 Cloud Run 使用本機 PersistentClient（存在 /tmp，可跨請求短暫復用）
    from chromadb.config import Settings
    chroma_client = chromadb.PersistentClient(path="/tmp/chroma", settings=Settings(allow_reset=True))
    print("✅ Using local Chroma PersistentClient at /tmp/chroma")
except Exception as e_local:
    print(f"⚠️ PersistentClient init failed: {e_local} — using in-memory client")
try:
    chroma_client = chromadb.Client()
    print("✅ Using in-memory Chroma client")
except Exception as e_mem:
    print(f"❌ In-memory Chroma init failed: {e_mem}")
    chroma_client = None
class AnalyzeRequest(BaseModel):
    url: str
    intent: str = None
    model_name: str = "gemini-1.5-flash"
    enable_rag: bool = False

# --- Helper Functions ---
def clean_html(html_content):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    for tag in soup(["script", "style", "nav", "footer", "iframe", "noscript", "svg", "button", "input", "form"]):
        tag.extract()
    text = soup.get_text(separator='\n')
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text[:50000], soup

def new_url_join(base, relative):
    from urllib.parse import urljoin
    return urljoin(base, relative)

# --- Generator 1: Scraper ---
def scrape_with_links_stream(url, max_depth=0):
    results = {"main": "", "related": {}}
    visited = set([url])
    
    yield {"type": "log", "msg": f"🕸️ Starting scraper on: {url}"}
    
    try:
        with sync_playwright() as p:
            # Stealth Config
            browser = p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled', '--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
            page = context.new_page()
            
            # 1. Main Page
            yield {"type": "log", "msg": f"📄 Fetching main page content..."}
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(2500)
            
            content = page.content()
            results["main"], _ = clean_html(content)
            yield {"type": "log", "msg": f"✅ Main page captured ({len(results['main'])} chars)"}

            # 2. Related Links
            if max_depth > 0 and len(results["main"]) > 100:
                yield {"type": "log", "msg": "🔍 Scanning for related legal documents..."}
                links = page.query_selector_all("a")
                found_links = []
                keywords = ["privacy", "policy", "terms", "usage", "guidelines", "data", "processing"]
                
                for link in links:
                    try:
                        href = link.get_attribute("href")
                        if not href or href.startswith(("#", "mailto:", "javascript:")): continue
                        text = link.inner_text().lower()
                        if any(k in text for k in keywords):
                            full_url = href if href.startswith("http") else new_url_join(url, href)
                            if full_url not in visited:
                                found_links.append((text, full_url))
                                visited.add(full_url)
                    except: pass
                
                # Scrape related
                # 這裡過濾掉重複的 URL (有些網站會有多個連結指向同一處)
                unique_links = list(dict.fromkeys([x[1] for x in found_links]))
                # 找回對應的 text
                final_links = []
                for u in unique_links:
                    for t, l in found_links:
                        if l == u:
                            final_links.append((t, l))
                            break

                total_links = min(len(final_links), 5)
                for i, (link_text, link_url) in enumerate(final_links[:5]):
                    yield {"type": "log", "msg": f"🔗 Crawling sub-page ({i+1}/{total_links}): {link_text[:20]}..."}
                    try:
                        sub_page = context.new_page()
                        sub_page.goto(link_url, timeout=20000, wait_until="domcontentloaded")
                        sub_page.wait_for_timeout(3000)
                        sub_text, _ = clean_html(sub_page.content())
                        if len(sub_text) > 100:
                            results["related"][link_url] = sub_text
                        sub_page.close()
                    except Exception as e:
                        yield {"type": "log", "msg": f"❌ Failed to crawl {link_url}"}

            browser.close()
            # 這裡回傳最終資料
            yield {"type": "data", "payload": results}
            
    except Exception as e:
        yield {"type": "error", "msg": str(e)}

# --- Generator 2: RAG Setup (Fixed Logic) ---
def setup_rag_db_stream(scraped_data, main_url):
    if not chroma_client: 
        yield {"type": "log", "msg": "⚠️ ChromaDB client not available, skipping RAG."}
        yield {"type": "db_ready", "collection": None, "name": None}
        return

    collection_name = f"session_{uuid.uuid4().hex}"
    yield {"type": "log", "msg": f"💾 Creating vector database: {collection_name}"}
    
    try:
        collection = chroma_client.create_collection(name=collection_name)
    except:
        chroma_client.delete_collection(name=collection_name)
        collection = chroma_client.create_collection(name=collection_name)
    
    documents, metadatas, ids = [], [], []
    # 組合 Main + Related
    all_pages = [(k, v) for k, v in scraped_data["related"].items()]
    all_pages.insert(0, (main_url, scraped_data["main"]))
    
    chunk_size, overlap = 1500, 200
    
    yield {"type": "log", "msg": f"🧩 Chunking text data from {len(all_pages)} sources..."}
    for source_url, text in all_pages:
        if not text: continue
        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i:i+chunk_size]
            if len(chunk) < 100: continue
            documents.append(chunk)
            metadatas.append({"source": source_url})
            ids.append(f"{uuid.uuid4().hex}")
            
    if not documents:
        yield {"type": "log", "msg": "⚠️ No valid text found to embed."}
        yield {"type": "db_ready", "collection": None, "name": None}
        return

    yield {"type": "log", "msg": f"🧠 Generating embeddings for {len(documents)} chunks using Gemini..."}
    
    embeddings = []
    batch_size = 10
    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i:i+batch_size]
        try:
            batch_result = genai.embed_content(
                model="models/text-embedding-004",
                content=batch_docs,
                task_type="retrieval_document"
            )
            embeddings.extend(batch_result['embedding'])
            if i % 20 == 0 and i > 0:
                 yield {"type": "log", "msg": f"   ...Processed {i}/{len(documents)} chunks"}
        except:
            # Fallback zero vectors
            embeddings.extend([[0.0]*768]*len(batch_docs))
        time.sleep(0.5)

    if documents:
        collection.add(documents=documents, embeddings=embeddings, metadatas=metadatas, ids=ids)
    
    yield {"type": "log", "msg": "✅ RAG Knowledge Base ready!"}
    
    # [修正點] 明確使用 yield 回傳物件，而不是 return
    yield {"type": "db_ready", "collection": collection, "name": collection_name}

# --- Main Orchestrator ---
def analyze_logic(req: AnalyzeRequest):
    model = genai.GenerativeModel(req.model_name)
    
    # 1. Scrape
    scrape_results = None
    depth = 1 if req.enable_rag else 0
    
    for event in scrape_with_links_stream(req.url, max_depth=depth):
        if event["type"] == "data":
            scrape_results = event["payload"]
        elif event["type"] == "error":
            yield json.dumps(event) + "\n"
            return
        else:
            yield json.dumps(event) + "\n"
            
    if not scrape_results or not scrape_results["main"]:
        yield json.dumps({"type": "error", "msg": "Failed to scrape main page"}) + "\n"
        return

    # 2. RAG Setup
    final_context = ""
    rag_chunks_for_display = []
    knowledge_base = [f"Main: {req.url}"] + [f"Related: {u}" for u in scrape_results["related"].keys()]
    used_sources = ["Main Page Only"]
    engine_info = "Playwright (Single Page)"
    col_name_to_delete = None

    if req.enable_rag and chroma_client:
        collection = None
        # Iterate RAG Generator
        for event in setup_rag_db_stream(scrape_results, req.url):
            if event["type"] == "log":
                yield json.dumps(event) + "\n"
            elif event["type"] == "db_ready":
                collection = event["collection"]
                col_name_to_delete = event["name"]
        
        if collection:
            yield json.dumps({"type": "log", "msg": "🤖 Retrieving relevant context for your intent..."}) + "\n"
            user_intent = req.intent if req.intent else "General legal risks"
            query_emb = genai.embed_content(model="models/text-embedding-004", content=user_intent, task_type="retrieval_query")['embedding']
            
            query_results = collection.query(query_embeddings=[query_emb], n_results=15)
            
            retrieved_chunks = query_results['documents'][0]
            retrieved_metadatas = query_results['metadatas'][0]
            
            context_parts = []
            sources_set = set()
            for chunk, meta in zip(retrieved_chunks, retrieved_metadatas):
                src = meta['source']
                sources_set.add(src)
                context_parts.append(f"=== SOURCE DOCUMENT: {src} ===\n{chunk}")
                if src != req.url:
                    rag_chunks_for_display.append(f"=== 📎 EXTRACT FROM: {src} ===\n{chunk}")
            
            final_context = "\n\n".join(context_parts)
            engine_info = f"Playwright + RAG | Sources: {len(sources_set)}"
            used_sources = list(sources_set)
        else:
            # RAG Failed (collection is None)
            yield json.dumps({"type": "log", "msg": "⚠️ RAG Setup failed (Collection None), falling back to single page."}) + "\n"
            final_context = f"=== SOURCE DOCUMENT: {req.url} ===\n{scrape_results['main'][:100000]}"
            engine_info = "Playwright (RAG Setup Failed)"
    else:
        final_context = f"=== SOURCE DOCUMENT: {req.url} ===\n{scrape_results['main'][:100000]}"

    # 3. Prompting
    yield json.dumps({"type": "log", "msg": "🧠 AI is analyzing risks (this may take a few seconds)..."}) + "\n"
    
    user_intent = req.intent if req.intent else "General Audit"

    # --- PROMPT REFINEMENT: Localization & Reality Check ---
    prompt = f"""
    You are a pragmatic legal assistant for general users.  
    Analyze the following Terms-of-Service (ToS) context based on the User Intent.

    【User Intent】: "{user_intent}"

    【ToS Context Source】:
    {final_context}

    Your task is to identify practical risks, NOT theoretical or unlikely legal dangers.  
    You must follow the rules below strictly.

    --------------------------------------------------------
    1. LANGUAGE RULES (MANDATORY)
    --------------------------------------------------------
    - All **analysis, explanations, and summaries** must be in **Traditional Chinese (繁體中文)**.
    - All **quotes** from the ToS must remain in **the original language**.  
    Do NOT translate or paraphrase quotes.

    --------------------------------------------------------
    2. RISK CALIBRATION RULES
    --------------------------------------------------------

    **Rule A: Industry-Standard Trade-offs = LOW**
    If the service is a common digital platform or app (e.g., messaging, cloud storage, AI tools) and the user intent is normal:
    - "Data used for personalization/ads/analytics/model improvement" → **Low**
    - "Data shared with affiliates/service providers" → **Low**
    - "Moderation, logging, security scanning" → **Low**
    - Rationale: These are standard trade-offs, NOT meaningful risks.

    **Rule B: Good-Faith User Assumption**
    Assume the user is a normal, compliant individual.
    - Do NOT list "fraud/abuse/illegal content" as risks.
    - Only include "account suspension/termination" if the **user intent** directly conflicts with ToS (e.g., automated scraping, reverse engineering, commercial misuse).

    --------------------------------------------------------
    3. SEVERITY DEFINITIONS
    --------------------------------------------------------

    - **HIGH (75-100)**: Directly prohibited actions.
    - The ToS explicitly bans the user's intent.
    - Likely to trigger suspension, legal action, or service denial.

    - **MEDIUM (35-74)**: Functional or usage constraints.
    - The action is allowed but restricted (e.g., commercial-use limitations, API quotas, licensing barriers).
    - Or unusually invasive data practices beyond industry norms.

    - **LOW (1-34)**: Standard boilerplate.
    - Privacy disclaimers.
    - Liability limitations.
    - Accuracy disclaimers.
    - Arbitration clauses.
    - Standard data collection for service operation.

    - **SAFE (0)**:
    - User intent fully matches expected usage.

    --------------------------------------------------------
    4. EVIDENCE & CITATION RULES (CRITICAL)
    --------------------------------------------------------
    - **Strict Alignment**: The "quote" field MUST be the direct evidence that supports the "point".
    - **No Hallucination**: If you cannot find an exact sentence in the source text to support a risk, DO NOT invent one. Instead, mark the risk as a "suggestion" or remove it.
    - **Source Tracking**: Ensure the "source_name" matches the document where the "quote" was found.
    
    --------------------------------------------------------
    JSON OUTPUT FORMAT
    --------------------------------------------------------

    {{
        "risk_score": (int) 0-100,
        "risk_level": "High" | "Medium" | "Low" | "Safe",
        "overview": "Summary in Traditional Chinese",
        "risks": [
            {{
                "point": "Risk description in Traditional Chinese",
                "severity": "High" | "Medium" | "Low",
                "quote": "Exact substring from the provided text that proves this point",
                "source_name": "Name/URL of the source or 'Main ToS'"
            }}
        ],
        "suggestions": [
            "Suggestion in Traditional Chinese",
            "..."
        ]
    }}

    """
    
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        result_json = json.loads(response.text)
        
        display_content = f"=== 🏠 MAIN DOCUMENT: {req.url} ===\n\n{scrape_results['main']}"
        if rag_chunks_for_display:
            display_content += "\n\n" + "="*50 + "\n=== 📚 RELATED CONTENT RETRIEVED BY RAG ===\n" + "="*50 + "\n\n" + "\n\n".join(rag_chunks_for_display)

        final_response = {
            "result": result_json,
            "scraped_content": display_content,
            "token_usage": {"total_token": response.usage_metadata.total_token_count},
            "debug_info": {
                "model": req.model_name,
                "url": req.url,
                "engine": engine_info,
                "knowledge_base": knowledge_base,
                "retrieved_sources": used_sources
            }
        }
        
        if col_name_to_delete and chroma_client:
            try: chroma_client.delete_collection(col_name_to_delete)
            except: pass
            
        yield json.dumps({"type": "result", "data": final_response}) + "\n"

    except Exception as e:
         yield json.dumps({"type": "error", "msg": str(e)}) + "\n"

@app.post("/analyze")
async def analyze_tos_endpoint(req: AnalyzeRequest):
    return StreamingResponse(analyze_logic(req), media_type="application/x-ndjson")

@app.get("/models")
def get_available_models():
    try:
        models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'gemini' in m.name:
                    clean_name = m.name.replace("models/", "")
                    models.append(clean_name)
        models.sort(reverse=True)
        return {"models": models}
    except Exception as e:
        print(f"Fetch models failed: {e}")
        return {"models": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"]}
        '''
        return {"models": ["gemini-robotics-er-1.5-preview",
            "gemini-pro-latest",
            "gemini-flash-lite-latest",
            "gemini-flash-latest",
            "gemini-exp-1206",
            "gemini-3-pro-preview",
            "gemini-3-pro-image-preview",
            "gemini-2.5-pro-preview-tts",
            "gemini-2.5-pro",
            "gemini-2.5-flash-preview-tts",
            "gemini-2.5-flash-preview-09-2025",
            "gemini-2.5-flash-lite-preview-09-2025",
            "gemini-2.5-flash-lite",
            "gemini-2.5-flash-image-preview",
            "gemini-2.5-flash-image",
            "gemini-2.5-flash",
            "gemini-2.5-computer-use-preview-10-2025",
            "gemini-2.0-flash-lite-preview-02-05",
            "gemini-2.0-flash-lite-preview",
            "gemini-2.0-flash-lite-001",
            "gemini-2.0-flash-lite",
            "gemini-2.0-flash-exp-image-generation",
            "gemini-2.0-flash-exp",
            "gemini-2.0-flash-001",
            "gemini-2.0-flash"]}
    # --- Health Check Endpoint (for Cloud Run) ---
@app.get("/health")
def health_check():
    """
    Health check endpoint for Cloud Run
    """
    return {
        "status": "healthy",
        "timestamp": time.time()
    }
    '''