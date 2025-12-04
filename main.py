from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime
import os
import uuid
import uvicorn

# ===== 初始化 FastAPI =====
app = FastAPI(title="EmoGo Backend API", version="1.0.0")

# ===== CORS 設定 =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== MongoDB 連線 =====
# ⚠️ 這裡要換成你「真的」的帳號密碼，不要有 < >
# 建議之後改成用環境變數讀取，現在先方便測試
MONGODB_URI = "mongodb+srv://fanany2666_db_user:yunyun33@emogo.pdnnisp.mongodb.net/"
DB_NAME = "emogo"

try:
    client = MongoClient(MONGODB_URI)
    db = client[DB_NAME]
    records_collection = db["records"]
    print("✅ Connected to MongoDB")
except Exception as e:
    print("❌ MongoDB connection failed:", e)
    # 先不 raise，讓 health endpoint 告訴你狀態

# ===== 影片儲存目錄 =====
UPLOAD_DIR = "vlogs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 掛載靜態檔案目錄（供影片下載）
app.mount("/vlogs", StaticFiles(directory=UPLOAD_DIR), name="vlogs")

# ===== 資料模型 =====
class RecordData(BaseModel):
    moodScore: int
    stressScore: int
    lat: float
    lng: float
    accuracy: float
    videoUrl: str
    timestamp: str

# ===== API 端點 =====

@app.get("/")
async def root():
    """根路徑：返回 API 基本資訊"""
    return {
        "message": "EmoGo Backend API",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "upload_video": "POST /upload/video",
            "upload_record": "POST /upload/record",
            "export_data": "GET /export"
        }
    }

@app.post("/upload/video")
async def upload_video(file: UploadFile = File(...)):
    """
    上傳影片檔案
    - 接收影片檔案（multipart/form-data）
    - 儲存至 vlogs/ 目錄
    - 回傳影片的公開 URL
    """
    try:
        # 生成唯一檔名
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # 儲存檔案
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # 本地測試用 base_url
        base_url = os.getenv("BASE_URL", "http://127.0.0.1:8000")
        video_url = f"{base_url}/vlogs/{unique_filename}"
        
        return {
            "success": True,
            "videoUrl": video_url,
            "filename": unique_filename,
            "message": "Video uploaded successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/upload/record")
async def upload_record(record: RecordData):
    """
    上傳使用者記錄
    - 接收 JSON 格式的心情、壓力、GPS、影片 URL 等資料
    - 儲存至 MongoDB
    """
    try:
        record_dict = record.dict()
        record_dict["created_at"] = datetime.utcnow()
        
        result = records_collection.insert_one(record_dict)
        
        return {
            "success": True,
            "record_id": str(result.inserted_id),
            "message": "Record saved successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Save failed: {str(e)}")

@app.get("/export")
async def export_data():
    """
    匯出所有資料：
    - 回傳 MongoDB records（心情、壓力、GPS、影片 URL）
    - 回傳 vlogs/ 目錄中所有可下載的影片
    """
    try:
        # ===== 1. 讀取 MongoDB records =====
        records = list(records_collection.find())
        for r in records:
            r["_id"] = str(r["_id"])
            if "created_at" in r:
                r["created_at"] = r["created_at"].isoformat()

        # ===== 2. 列出所有 vlog 檔案 =====
        vlog_list = []
        base_url = os.getenv("BASE_URL", "http://127.0.0.1:8000")

        for filename in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, filename)

            if os.path.isfile(file_path):
                vlog_list.append({
                    "filename": filename,
                    "url": f"{base_url}/vlogs/{filename}",
                    "size": os.path.getsize(file_path),
                    "modified_at": datetime.fromtimestamp(
                        os.path.getmtime(file_path)
                    ).isoformat()
                })

        return {
            "success": True,
            "total_records": len(records),
            "records": records,
            "vlogs": vlog_list,
            "exported_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    try:
        client.admin.command("ping")
        return {
            "status": "healthy",
            "mongodb": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "mongodb": "disconnected",
            "error": str(e)
        }

# ===== 啟動伺服器（本地測試用） =====
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
