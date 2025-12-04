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
    """上傳影片檔案"""
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
    """上傳紀錄資料"""
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

from fastapi.responses import StreamingResponse
import io
import zipfile
import json

@app.get("/download/all")
async def download_all():
    """
    打包所有紀錄 + 所有影片為 ZIP 檔
    """
    try:
        # 讀取所有紀錄
        records = await app.db["records"].find().to_list(99999)
        for r in records:
            r["_id"] = str(r["_id"])
            if "created_at" in r:
                r["created_at"] = r["created_at"].isoformat()

        # 建立記憶體中的 zip buffer
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:

            # 加入 records.json
            zip_file.writestr("records.json", json.dumps(records, indent=2))

            # 加入所有影片
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    zip_file.write(file_path, f"videos/{filename}")

        zip_buffer.seek(0)

        # 回傳 ZIP
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": "attachment; filename=emogo_export.zip"
            }
        )

    except Exception as e:
        raise HTTPException(500, f"Download failed: {e}")

@app.get("/export")
async def export_data():
    '''匯出所有紀錄與影片列表'''
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
    """檢查能否連線到 MongoDB"""
    try:
        await app.db.command("ping")
        return {"status": "healthy"}
    except:
        return {"status": "unhealthy"}

@app.get("/records/filter/mood")
async def filter_by_mood(min: int = None, max: int = None):
    """根據心情分數範圍查詢紀錄
     min: 最小心情分數
     max: 最大心情分數
    """
    query = {}
    if min is not None:
        query["moodScore"] = {"$gte": min}
    if max is not None:
        query.setdefault("moodScore", {})
        query["moodScore"]["$lte"] = max

    records = await app.db["records"].find(query).to_list(99999)
    for r in records:
        r["_id"] = str(r["_id"])
    return {"count": len(records), "records": records}

@app.get("/records/filter/stress")
async def filter_by_stress(min: int = None, max: int = None):
    """根據壓力分數範圍查詢紀錄
     min: 最小壓力分數
     max: 最大壓力分數
    """
    query = {}
    if min is not None:
        query["stressScore"] = {"$gte": min}
    if max is not None:
        query.setdefault("stressScore", {})
        query["stressScore"]["$lte"] = max

    records = await app.db["records"].find(query).to_list(99999)
    for r in records:
        r["_id"] = str(r["_id"])
    return {"count": len(records), "records": records}
@app.get("/records/filter/date")
async def filter_by_date(date: str):
    """
    根據日期查詢紀錄（含 GPS、心情、影片）
    timestamp 格式: "2025-01-15T10:30:00Z
    date 格式: "2025-01-15"
    """
    query = {"timestamp": {"$regex": f"^{date}"}}
    records = await app.db["records"].find(query).to_list(99999)

    for r in records:
        r["_id"] = str(r["_id"])
    return {"date": date, "count": len(records), "records": records}
@app.get("/records/filter/date-range")
async def filter_by_date_range(start: str, end: str):
    """
    查詢時間區間的紀錄（含 GPS、心情、影片）
    日期格式：YYYY-MM-DD
    e.g. /records/filter/date-range?start=2025-01-01&end=2025-01-05
    """
    try:
        # 使用正規表示法匹配 timestamp 前 10 字（YYYY-MM-DD）
        query = {
            "timestamp": {
                "$gte": start,
                "$lte": end
            }
        }

        records = await app.db["records"].find(query).to_list(99999)

        for r in records:
            r["_id"] = str(r["_id"])
            if "created_at" in r:
                r["created_at"] = r["created_at"].isoformat()

        return {
            "success": True,
            "start": start,
            "end": end,
            "count": len(records),
            "records": records
        }

    except Exception as e:
        raise HTTPException(500, f"Date range query failed: {e}")

@app.get("/records/filter/all")
async def filter_records_all(
    min_mood: int = None,
    max_mood: int = None,
    min_stress: int = None,
    max_stress: int = None,
    start: str = None,
    end: str = None,
    lat_min: float = None,
    lat_max: float = None,
    lng_min: float = None,
    lng_max: float = None,
):
    """
    複合式篩選：
    - moodScore
    - stressScore
    - 日期區間 (timestamp)
    - 緯度 / 經度區間
    """
    try:
        query = {}

        # mood filter
        if min_mood is not None:
            query["moodScore"] = {"$gte": min_mood}
        if max_mood is not None:
            query.setdefault("moodScore", {})
            query["moodScore"]["$lte"] = max_mood

        # stress filter
        if min_stress is not None:
            query["stressScore"] = {"$gte": min_stress}
        if max_stress is not None:
            query.setdefault("stressScore", {})
            query["stressScore"]["$lte"] = max_stress

        # date range filter
        if start and end:
            query["timestamp"] = {"$gte": start, "$lte": end}

        # latitude filter
        if lat_min is not None:
            query["lat"] = {"$gte": lat_min}
        if lat_max is not None:
            query.setdefault("lat", {})
            query["lat"]["$lte"] = lat_max

        # longitude filter
        if lng_min is not None:
            query["lng"] = {"$gte": lng_min}
        if lng_max is not None:
            query.setdefault("lng", {})
            query["lng"]["$lte"] = lng_max

        # run query
        records = await app.db["records"].find(query).to_list(99999)

        for r in records:
            r["_id"] = str(r["_id"])

        return {
            "success": True,
            "filters_applied": {
                "min_mood": min_mood,
                "max_mood": max_mood,
                "min_stress": min_stress,
                "max_stress": max_stress,
                "start": start,
                "end": end,
                "lat_min": lat_min,
                "lat_max": lat_max,
                "lng_min": lng_min,
                "lng_max": lng_max
            },
            "count": len(records),
            "records": records
        }

    except Exception as e:
        raise HTTPException(500, f"Composite filter failed: {e}")


@app.get("/stats/summary")
async def stats_summary():
    """
    回傳情緒、壓力等統計資訊：
    - 平均 moodScore / stressScore
    - 數量分布
    - 第一筆 / 最新一筆記錄時間
    """
    try:
        records = await app.db["records"].find().to_list(99999)
        if not records:
            return {"success": True, "message": "No records found."}

        # extract all values
        moods = [r["moodScore"] for r in records]
        stress = [r["stressScore"] for r in records]
        timestamps = [r["timestamp"] for r in records]

        # distribution for scores from 1 to 5
        mood_dist = {i: 0 for i in range(1, 6)}
        stress_dist = {i: 0 for i in range(1, 6)}

        for m in moods:
            if 1 <= m <= 5:
                mood_dist[m] += 1

        for s in stress:
            if 1 <= s <= 5:
                stress_dist[s] += 1

        summary = {
            "success": True,
            "total_records": len(records),
            "avg_moodScore": sum(moods) / len(moods),
            "avg_stressScore": sum(stress) / len(stress),
            "mood_distribution": mood_dist,
            "stress_distribution": stress_dist,
            "first_record_at": min(timestamps),
            "latest_record_at": max(timestamps),
        }

        return summary

    except Exception as e:
        raise HTTPException(500, f"Stats failed: {e}")


from bson import ObjectId
from urllib.parse import urlparse

@app.delete("/records/{record_id}")
async def delete_record(record_id: str):
    """
    刪除一筆紀錄 + 刪除對應影片
    """
    try:
        # 1. 讀取該筆資料
        record = await app.db["records"].find_one({"_id": ObjectId(record_id)})
        if not record:
            raise HTTPException(404, "Record not found")

        # 2. 刪除 MongoDB 內的資料
        await app.db["records"].delete_one({"_id": ObjectId(record_id)})

        # 3. 解析影片 filename，例如從 URL 中取出最後一段
        video_url = record.get("videoUrl")
        if video_url:
            filename = video_url.split("/")[-1]  # 最後一段就是檔名
            file_path = os.path.join(UPLOAD_DIR, filename)

            # 4. 刪除影片檔案
            if os.path.isfile(file_path):
                os.remove(file_path)

        return {
            "success": True,
            "deleted_record": record_id,
            "deleted_video": filename if video_url else None
        }

    except Exception as e:
        raise HTTPException(500, f"Delete failed: {e}")


@app.delete("/videos/{filename}")
async def delete_vlog(filename: str):
    """
    刪除單一影片檔案
    參數 filename 為檔案名稱，不含路徑
    """
    file_path = os.path.join(UPLOAD_DIR, filename)

    # 檢查檔案是否存在
    if not os.path.isfile(file_path):
        raise HTTPException(404, "File not found")

    try:
        os.remove(file_path)
        return {
            "success": True,
            "deleted_file": filename
        }

    except Exception as e:
        raise HTTPException(500, f"Delete failed: {e}")



@app.delete("/records/delete/all")
async def delete_all_records():
    """
    刪除所有紀錄 + 所有影片檔案
    """
    try:
        # 刪除 MongoDB 所有紀錄
        await app.db["records"].delete_many({})

        # 刪除全部影片
        for filename in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

        return {
            "success": True,
            "message": "All records and videos have been deleted."
        }

    except Exception as e:
        raise HTTPException(500, f"Delete all failed: {e}")


# ===== 啟動（本地） =====
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
