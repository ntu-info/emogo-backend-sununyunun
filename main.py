from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
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
MONGODB_URI = "mongodb+srv://fanany2666_db_user:yunyun33@emogo.pdnnisp.mongodb.net/"
DB_NAME = "emogo"

@app.on_event("startup")
async def startup_db():
    app.mongodb_client = AsyncIOMotorClient(MONGODB_URI)
    app.db = app.mongodb_client[DB_NAME]
    print("✅ MongoDB connected")

# ===== 影片儲存目錄 =====
UPLOAD_DIR = "vlogs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 掛載靜態檔案目錄
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

# ===== API =====

@app.get("/")
async def root():
    return {
        "message": "EmoGo Backend API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.post("/upload/video")
async def upload_video(file: UploadFile = File(...)):
    try:
        file_ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        base_url = os.getenv("BASE_URL", "http://127.0.0.1:8000")
        video_url = f"{base_url}/vlogs/{filename}"

        return {
            "success": True,
            "videoUrl": video_url,
            "filename": filename,
        }

    except Exception as e:
        raise HTTPException(500, f"Upload failed: {e}")


@app.post("/upload/record")
async def upload_record(record: RecordData):
    try:
        record_dict = record.dict()
        record_dict["created_at"] = datetime.utcnow()

        result = await app.db["records"].insert_one(record_dict)

        return {
            "success": True,
            "record_id": str(result.inserted_id),
        }

    except Exception as e:
        raise HTTPException(500, f"Save failed: {e}")


@app.get("/export")
async def export_data():
    try:
        # 1. 讀取 MongoDB
        records = await app.db["records"].find().to_list(99999)
        for r in records:
            r["_id"] = str(r["_id"])
            r["created_at"] = r["created_at"].isoformat()

        # 2. 列出所有 vlogs
        base_url = os.getenv("BASE_URL", "http://127.0.0.1:8000")
        vlog_list = []

        for filename in os.listdir(UPLOAD_DIR):
            path = os.path.join(UPLOAD_DIR, filename)
            if os.path.isfile(path):
                vlog_list.append({
                    "filename": filename,
                    "url": f"{base_url}/vlogs/{filename}",
                    "size": os.path.getsize(path),
                    "modified_at": datetime.fromtimestamp(os.path.getmtime(path)).isoformat()
                })

        return {
            "success": True,
            "records": records,
            "vlogs": vlog_list,
            "exported_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(500, f"Export failed: {e}")


@app.get("/health")
async def health_check():
    try:
        await app.db.command("ping")
        return {"status": "healthy"}
    except:
        return {"status": "unhealthy"}


# ===== 啟動（本地） =====
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
