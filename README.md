# EmoGo Backend API

EmoGo 是一個情緒、壓力與 GPS 記錄系統的後端服務，
提供 影片上傳、紀錄儲存、資料查詢、篩選、刪除、匯出 等功能。
本後端部署於 Render，作為 EmoGo App 的資料中心。

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
### 5. 刪除單一影片

**Endpoint:** `DELETE /videos/{filename}`

**描述:** 刪除 vlogs/ 中指定檔案。

---
### 6.刪除單一記錄 + 同步刪除影片

**Endpoint:** `DELETE /records/{record_id}`

**描述:** 

- 刪除 MongoDB 中的紀錄

- 自動解析該紀錄的 videoUrl

- 刪除對應的影片檔案

**Response:**
```
{
  "success": true,
  "deleted_record": "507f1f77bcf86cd799439011",
  "deleted_video": "abc.mp4"
}
```
---
### 7.刪除全部記錄 + 全部影片

**Endpoint:** `DELETE /records/delete/all`

---

### 8.複合式查詢

**Endpoint:** `GET /records/filter/all`

**描述:** 
支援以下參數（全部可自由組合）：
| Query Key  | 說明                |
| ---------- | ----------------- |
| min_mood   | 最低心情（1–5）         |
| max_mood   | 最高心情（1–5）         |
| min_stress | 最低壓力（1–5）         |
| max_stress | 最高壓力（1–5）         |
| start      | 起始日期 (YYYY-MM-DD) |
| end        | 結束日期 (YYYY-MM-DD) |
| lat_min    | 緯度下限              |
| lat_max    | 緯度上限              |
| lng_min    | 經度下限              |
| lng_max    | 經度上限              |

---
### 9.統計

**Endpoint:** `GET /stats/summary`

**描述:** 

內容包含：

total_records：總筆數

avg_moodScore：平均心情（1–5）

avg_stressScore：平均壓力（1–5）

mood_distribution：心情分布（1–5）

stress_distribution：壓力分布（1–5）

first_record_at：第一筆 timestamp

latest_record_at：最新一筆 timestamp

---
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
