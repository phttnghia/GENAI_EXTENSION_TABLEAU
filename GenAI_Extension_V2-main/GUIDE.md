# Hướng dẫn sử dụng Tableau Extension với FastAPI

## Tổng quan kiến trúc

```
┌─────────────────┐         ┌──────────────────┐         ┌────────────────┐         ┌──────────────────┐
│  Tableau        │         │  FastAPI Server  │         │   Azure SQL    │         │  Backend API     │
│  Dashboard      │ ──────> │  (Port 8000)     │ ──────> │   Database     │         │  (Port 7071)     │
│  (app.js)       │         │  (server.py)     │         │                │         │                  │
└─────────────────┘         └──────────────────┘         └────────────────┘         └──────────────────┘
        │                            │                            │                          │
        │  1. Gửi filters            │  2. Query data             │                          │
        │     từ dashboard           │     với WHERE clause       │                          │
        │                            │                            │                          │
        │                            │  3. Transform data         │                          │
        │                            │     (EAV → Wide format)    │                          │
        │                            │                            │                          │
        │                            │  4. Build JSON payload ────────────────────────────> │
        │                            │                                                       │
        │                            │  5. Nhận response <─────────────────────────────────┘
        │                            │                                                       
        │  6. Trả về UI <────────────┘                                                       
        │                                                                                    
```

## Luồng xử lý chi tiết

### 1. Frontend (app.js)
- Thu thập filters từ Tableau Dashboard
- Gửi request đến FastAPI server (port 8000)

### 2. FastAPI Server (server.py)
**BƯỚC 1-2: Query Database**
- Nhận filters từ frontend
- Map filter names sang column names trong database
- Build WHERE clause động
- Query data từ Azure SQL Database

**BƯỚC 3: Process Data**
- Transform data từ EAV format sang Wide format
- Pivot metrics theo date
- Clean và validate data

**BƯỚC 4: Build Payload**
- Tạo JSON payload với cấu trúc chuẩn
- Normalize filter names
- Add metadata (request_id, timestamp, etc.)

**BƯỚC 5: Call Backend API**
- Gửi payload đến Backend API (port 7071)
- Endpoint: `http://localhost:7071/api/analyze`

**BƯỚC 6: Return Response**
- Nhận response từ Backend API
- Forward response về frontend

### 3. Backend API (Port 7071) - Do team backend quản lý
- Nhận payload JSON
- Xử lý logic (AI, analysis, etc.)
- Trả về response

## Cài đặt

### 1. Cài đặt Python dependencies

```powershell
pip install -r requirements.txt
```

### 2. Cấu hình môi trường

Tạo file `.env` với nội dung:

```env
AZURE_SQL_DRIVER={ODBC Driver 17 for SQL Server}
AZURE_SQL_SERVER=your-server.database.windows.net
AZURE_SQL_DATABASE=your-database
AZURE_SQL_USER=your-username
AZURE_SQL_PASSWORD=your-password
AZURE_CONNECT_TIMEOUT=30
```

### 3. Chạy FastAPI server

```powershell
# Development mode (với auto-reload)
uvicorn server:app --reload --port 8000

# Production mode
uvicorn server:app --port 8000
```

Server sẽ chạy tại: `http://localhost:8000`

## Cấu trúc JSON Payload

### Request từ Frontend → FastAPI

```json
{
  "request_meta": {
    "mode_type": "Analyze Report"
  },
  "period": {
    "start_date": null,
    "end_date": null
  },
  "filters": {
    "Project Identifier": ["PROJECT_A"],
    "Redmine Infra": ["INFRA_1"],
    "Filter 1 (Vw Bug Report By Testplan)": ["Value1", "Value2"]
  },
  "mode_type": "Analyze Report",
  "user_question": "Optional - chỉ có khi mode_type = AI Assistant"
}
```

### Payload từ FastAPI → Backend API (Port 7071)

```json
{
  "request_meta": {
    "request_id": "req_a1b2c3d4e5f6",
    "timestamp": "2026-02-03T10:30:00Z",
    "mode_type": "Analyze Report"
  },
  "period": {
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  },
  "filters": {
    "project_identifier": ["PROJECT_A"],
    "redmine_infra": ["INFRA_1"],
    "filter_1": ["Value1", "Value2"]
  },
  "metrics_data": [
    {
      "date": "2024-01-01",
      "TestCaseActual": 100,
      "BReportActual": 10,
      "BReportFixed": 5,
      ...
    },
    {
      "date": "2024-01-02",
      "TestCaseActual": 120,
      "BReportActual": 12,
      "BReportFixed": 6,
      ...
    }
  ],
  "user_question": "Optional - chỉ có khi mode_type = AI Assistant"
}
```

## Mapping Configuration

### Filter Mapping (FILTER_COLUMN_MAPPING)
Map tên filter từ Tableau UI sang column trong database:

```python
FILTER_COLUMN_MAPPING = {
    "Project Identifier": "project_identifier",
    "Redmine Infra": "redmine_infra",
    "Redmine Server": "redmine_server",
    "Redmine Instance": "redmine_instance",
    "Filter 1 (Vw Bug Report By Testplan)": "filter_1",
    "Filter 2 (Vw Bug Report By Testplan)": "filter_2",
    # ... thêm mapping theo nhu cầu
}
```

### Display Name Mapping (FILTER_DISPLAY_NAME_MAPPING)
Map tên filter sang tên ngắn gọn trong JSON payload:

```python
FILTER_DISPLAY_NAME_MAPPING = {
    "Project Identifier": "project_identifier",
    "Redmine Infra": "redmine_infra",
    "Filter 1 (Vw Bug Report By Testplan)": "filter_1",
    # ... tương tự
}
```

### Metric Mapping (METRIC_VALUE_MAPPING)
Map metric names từ database sang key trong JSON output:

```python
METRIC_VALUE_MAPPING = {
    "TestCaseActual": "TestCaseActual",
    "BReportActual": "BReportActual",
    "BReportFixed": "BReportFixed",
    # ... thêm metrics theo nhu cầu
}
```

## Cấu hình Backend API

Để thay đổi URL của Backend API, cập nhật trong [server.py](server.py):

```python
# Backend API Configuration
BACKEND_API_URL = "http://localhost:7071/api"  # Thay đổi URL nếu cần
BACKEND_API_ENDPOINT = f"{BACKEND_API_URL}/analyze"  # Endpoint của team backend
```

## Testing

### Test FastAPI server

```powershell
# Kiểm tra server đang chạy
curl http://localhost:8000

# Test API endpoint
curl -X POST http://localhost:8000/ask-ai `
  -H "Content-Type: application/json" `
  -d '{
    "filters": {"Project Identifier": ["TEST"]},
    "period": {"start_date": null, "end_date": null},
    "mode_type": "Analyze Report"
  }'
```

### View API documentation

FastAPI tự động tạo interactive API docs:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Lưu ý quan trọng

1. **Port Configuration**
   - FastAPI Server: 8000
   - Backend API: 7071

2. **Backend API Endpoint**
   - Team backend cần cung cấp endpoint chính xác
   - Mặc định: `http://localhost:7071/api/analyze`

3. **Filter Names**
   - Phải match chính xác với tên trong Tableau Dashboard
   - Phải có mapping trong `FILTER_COLUMN_MAPPING`

4. **Database View**
   - View name: `vw_bug_report_by_testplan`
   - Schema: `bug-management_dm_test`
   - Cấu trúc EAV: date, Metric_Name, Metric_Value

5. **Error Handling**
   - Server sẽ forward error từ Backend API
   - Check logs để debug

## Troubleshooting

### Server không khởi động
```powershell
# Kiểm tra port 8000 có bị chiếm không
netstat -ano | findstr :8000

# Kill process nếu cần
taskkill /PID <PID> /F
```

### Không connect được database
- Kiểm tra `.env` file có đúng thông tin
- Test connection bằng `check_view.py`

### Backend API không response
- Kiểm tra Backend API đang chạy ở port 7071
- Kiểm tra URL endpoint có đúng không
- Check logs của Backend API

### Filter không hoạt động
- Kiểm tra tên filter có match với `FILTER_COLUMN_MAPPING`
- Check column names trong database view
- Xem logs để debug SQL query

## Liên hệ

- Frontend/Extension: Tableau Extension (app.js)
- Middleware: FastAPI Server (server.py) - Port 8000
- Backend API: Team Backend - Port 7071
