# EmoGo Backend API

EmoGo 是一個情緒與壓力記錄系統的後端服務，提供影片上傳、記錄儲存與資料匯出功能。

## 📌 重要連結
### 📱 APP URL
```
https://expo.dev/accounts/feengyun/projects/emo-go-app/builds/575b1fe3-0e1a-4747-bf45-b1b61b3a36d7
```

### 🌐 Public Backend URL
```
https://emogo-backend-sununyunun.onrender.com
```

### 📥 Export URL
```
https://emogo-backend-sununyunun.onrender.com/export
```

### 📖 API 文件 (助教請用這個看 ><)
```
https://emogo-backend-sununyunun.onrender.com/docs
```

---

## 🚀 API 說明

### 1. 上傳影片
**Endpoint:** `POST /upload/video`

**描述:** 上傳影片檔案，回傳影片的公開 URL

**Request (multipart/form-data):**
```
file: (影片檔案)
```

**Response:**
```json
{
  "success": true,
  "videoUrl": "https://your-app.onrender.com/vlogs/xxx.mp4",
  "filename": "xxx.mp4",
  "message": "Video uploaded successfully"
}
```

---

### 2. 上傳記錄
**Endpoint:** `POST /upload/record`

**描述:** 儲存使用者的心情、壓力、GPS 與影片資訊

**Request (JSON):**
```json
{
  "moodScore": 8,
  "stressScore": 3,
  "lat": 25.0330,
  "lng": 121.5654,
  "accuracy": 10.5,
  "videoUrl": "https://your-app.onrender.com/vlogs/xxx.mp4",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

**Response:**
```json
{
  "success": true,
  "record_id": "507f1f77bcf86cd799439011",
  "message": "Record saved successfully"
}
```

---

### 3. 匯出所有資料
**Endpoint:** `GET /export`

**描述:** 取得所有記錄（供助教下載檢查）

**Response:**
```json
{
  "success": true,
  "total_records": 42,
  "data": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "moodScore": 8,
      "stressScore": 3,
      "lat": 25.0330,
      "lng": 121.5654,
      "accuracy": 10.5,
      "videoUrl": "https://your-app.onrender.com/vlogs/xxx.mp4",
      "timestamp": "2025-01-15T10:30:00Z",
      "created_at": "2025-01-15T10:35:22Z"
    }
  ],
  "exported_at": "2025-01-20T14:20:00Z"
}
```

---

### 4. 健康檢查
**Endpoint:** `GET /health`

**描述:** 檢查後端與 MongoDB 連線狀態

---

## 🔧 本地開發

### 安裝相依套件
```bash
pip install -r requirements.txt
```

### 設定環境變數
```bash
export MONGO_URI="mongodb://localhost:27017"
export BASE_URL="http://localhost:8000"
```

### 啟動伺服器
```bash
python main.py
```

### 存取 API 文件
```
http://localhost:8000/docs
```

---

## 📊 資料結構

### MongoDB Collection: `records`
```json
{
  "_id": ObjectId,
  "moodScore": Number,      // 心情分數 (1-10)
  "stressScore": Number,    // 壓力分數 (1-10)
  "lat": Number,            // 緯度
  "lng": Number,            // 經度
  "accuracy": Number,       // GPS 精確度
  "videoUrl": String,       // 影片 URL
  "timestamp": String,      // 使用者記錄時間
  "created_at": DateTime    // 後端儲存時間
}
