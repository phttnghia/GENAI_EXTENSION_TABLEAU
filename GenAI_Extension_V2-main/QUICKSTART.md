# Quick Start Guide

## Current Status ✅

✅ **Frontend (app.js)** - Working
✅ **FastAPI Server (server.py)** - Working  
✅ **Payload Building** - Working
⚠️ **Backend API (port 7071)** - Not running yet

## What You Have Now

Your system successfully:
1. ✅ Collects filters from Tableau Dashboard
2. ✅ Queries database with WHERE conditions
3. ✅ Builds JSON payload with metrics data
4. ⚠️ Ready to send to Backend API (but API is not running)

## Solution 1: DEBUG MODE (Recommended for now)

**Current Setting:** `DEBUG_MODE = True` in [server.py](server.py#L23)

This means:
- ✅ System will build the payload
- ✅ System will return payload directly WITHOUT calling Backend API
- ✅ You can inspect the payload structure
- ⚠️ No actual Backend API call

### To Test:
1. Start FastAPI server:
   ```powershell
   uvicorn server:app --reload --port 8000
   ```

2. Open Tableau Extension and click "Analyze"

3. You'll see:
   - Payload in UI (formatted JSON)
   - Success message with payload details
   - No Backend API error

## Solution 2: Wait for Backend API Team

When Backend API team is ready:

1. Make sure Backend API is running on port 7071
2. Test connection:
   ```powershell
   python test_backend_api.py
   ```

3. If test passes, set in [server.py](server.py#L23):
   ```python
   DEBUG_MODE = False  # Enable real Backend API call
   ```

4. Restart FastAPI server

## Solution 3: Test Backend API Connection

Run the test script:
```powershell
python test_backend_api.py
```

**If Backend API is running:**
```
✅ Response Status: 200
✅ BACKEND API IS RUNNING AND ACCESSIBLE!
```

**If Backend API is NOT running:**
```
❌ Connection Failed!
⚠️ BACKEND API IS NOT RUNNING
```

## Expected Flow

### With DEBUG_MODE = True (Current)
```
Tableau → FastAPI Server → Build Payload → Return Payload
                                           (Skip Backend API)
```

### With DEBUG_MODE = False (Production)
```
Tableau → FastAPI Server → Build Payload → Backend API (7071) → Response → Frontend
```

## Next Steps

1. ✅ Keep DEBUG_MODE = True for now
2. ✅ Verify payload structure is correct
3. ⏳ Wait for Backend API team to confirm endpoint
4. ⏳ Test Backend API connection
5. ⏳ Switch DEBUG_MODE = False
6. ✅ Full integration test

## Files Modified

- ✅ [server.py](server.py) - Added DEBUG_MODE
- ✅ [app.js](app.js) - Added debug logs
- ✅ [test_backend_api.py](test_backend_api.py) - New test script

## Configuration

### Backend API Endpoint
File: [server.py](server.py#L21-L22)
```python
BACKEND_API_URL = "http://localhost:7071/api"
BACKEND_API_ENDPOINT = f"{BACKEND_API_URL}/analyze"
```

Change this if Backend API team uses different URL/port.

### Debug Mode
File: [server.py](server.py#L25)
```python
DEBUG_MODE = True  # Change to False for production
```

## Contact Backend API Team

Questions to ask:
1. ✅ Confirm endpoint URL: `http://localhost:7071/api/analyze`?
2. ✅ Is the endpoint ready?
3. ✅ What response format will they return?
4. ✅ Any authentication required?

## Payload Structure (Ready to Send)

Your system generates this payload format:

```json
{
  "request_meta": {
    "request_id": "req_abc123...",
    "timestamp": "2026-02-03T10:30:00Z",
    "mode_type": "Analyze Report"
  },
  "period": {
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  },
  "filters": {
    "project_identifier": ["VALUE"],
    "redmine_infra": ["VALUE"]
  },
  "metrics_data": [
    {
      "date": "2024-01-01",
      "TestCaseActual": 100,
      "BReportActual": 10,
      ...
    }
  ]
}
```

This is exactly what Backend API will receive when DEBUG_MODE = False.
