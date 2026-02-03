from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import pandas as pd
import pyodbc
import os
import json
from datetime import datetime
from config.settings import settings
import uuid
import httpx

app = FastAPI(title="Tableau Extension API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# 1. CẤU HÌNH
# ==============================================================================

# Backend API Configuration
# Azure Functions routePrefix is empty in backend host.json
BACKEND_API_BASE_URL = os.getenv("BACKEND_API_BASE_URL", "http://localhost:7071")
BACKEND_API_PREFIX = os.getenv("BACKEND_API_PREFIX", "/api/v1")

ANALYSIS_API_ENDPOINT = f"{BACKEND_API_BASE_URL}{BACKEND_API_PREFIX}/analysis"
ASSISTANT_API_ENDPOINT = f"{BACKEND_API_BASE_URL}{BACKEND_API_PREFIX}/assistant"

# Backend API Auth (override via environment variables)
BACKEND_API_KEY = os.getenv("BACKEND_API_KEY", "EXPECTED_API_KEY")
BACKEND_JWT_TOKEN = os.getenv("BACKEND_JWT_TOKEN", "123-dev-token")

# Code debug for: Skip backend API call and return payload directly (set to true via DEBUG_MODE env var)
# DISABLED: Changed to always False to show real backend response
DEBUG_MODE = False  # os.getenv("DEBUG_MODE", "false").lower() == "true"

DB_VIEW_NAME = "vw_bug_report_by_testplan" 
DB_SCHEMA_NAME = "bug-management_dm_test"  

# 1. Mapping Filter: Tên Filter UI -> Tên Cột DB (Dùng cho WHERE clause)
FILTER_COLUMN_MAPPING = {
    "Project Identifier": "project_identifier",
    "Redmine Infra": "redmine_infra",
    "Redmine Server": "redmine_server",
    "Redmine Instance": "redmine_instance",
    "Filter 1 (Vw Bug Report By Testplan)": "filter_1",
    "Filter 2 (Vw Bug Report By Testplan)": "filter_2",
    "Filter 3 (Vw Bug Report By Testplan)": "filter_3",
    "Filter 4 (Vw Bug Report By Testplan)": "filter_4",
    "Filter 5 (Vw Bug Report By Testplan)": "filter_5"
}

# 1b. Mapping Filter Display Name: Tên Filter UI -> Tên hiển thị trong JSON (Dùng cho Response)
# Dùng để normalize filter names trong JSON response
FILTER_DISPLAY_NAME_MAPPING = {
    "Project Identifier": "project_identifier",
    "Redmine Infra": "redmine_infra",
    "Redmine Server": "redmine_server",
    "Redmine Instance": "redmine_instance",
    "project_name (Custom SQL Query)": "project_name",
    "Filter 1 (Vw Bug Report By Testplan)": "filter_1",
    "Filter 2 (Vw Bug Report By Testplan)": "filter_2",
    "Filter 3 (Vw Bug Report By Testplan)": "filter_3",
    "Filter 4 (Vw Bug Report By Testplan)": "filter_4",
    "Filter 5 (Vw Bug Report By Testplan)": "filter_5"
}

# 2. Mapping Metric Name: Giá trị trong cột Metric_Name (DB) -> Key trong JSON (Output)
# Cách dùng: Khi Pivot, cột Metric_Name sẽ được map sang key này trong JSON output
# Ví dụ: DB có Metric_Name='TestCaseActual' -> JSON output sẽ có key 'TestCaseActual': <giá trị>
# NẾU BẠN MUỐN ĐỔI TÊN: Chỉ cần sửa value bên phải
# Ví dụ: "TestCaseActual": "Test_Case_Actual" (nếu muốn snake_case)
METRIC_VALUE_MAPPING = {
    "TestCaseExpected": "TestCaseExpected",
    "TestCaseExpectedTotal": "TestCaseExpectedTotal",
    "TestCaseActual": "TestCaseActual",
    "TestCaseActualTotal": "TestCaseActualTotal",
    "BReportExpected": "BReportExpected",
    "BReportExpectedTotal": "BReportExpectedTotal",
    "BReportActual": "BReportActual",
    "BReportActualTotal": "BReportActualTotal",
    "BReportFixed": "BReportFixed",
    "BReportFixedTotal": "BReportFixedTotal",
    "BReportOutstanding": "BReportOutstanding",
    "BReportUpperBound": "BReportUpperBound",
    "BReportLowerBound": "BReportLowerBound"
}

# ==============================================================================
# 2. PYDANTIC MODELS
# ==============================================================================

class PeriodModel(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class RequestMetaModel(BaseModel):
    mode_type: Optional[str] = "Analyze Report"

class RequestPayload(BaseModel):
    request_meta: Optional[RequestMetaModel] = RequestMetaModel()
    period: Optional[PeriodModel] = PeriodModel()
    filters: Dict[str, Any] = {}
    mode_type: Optional[str] = "Analyze Report"
    user_question: Optional[str] = None



# ==============================================================================
# 3. HỖ TRỢ HÀM
# ==============================================================================

def generate_request_id():
    """Generate unique request ID"""
    return f"req_{uuid.uuid4().hex[:12]}"

def get_iso_timestamp():
    """Get current timestamp in ISO 8601 format"""
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


# ==============================================================================
# 4. DATABASE CONNECTION
# ==============================================================================
def get_db_connection():
    """Get database connection"""
    try:
        conn_str = (
            f"DRIVER={settings.AZURE_SQL_DRIVER};"
            f"SERVER={settings.AZURE_SQL_SERVER};"
            f"DATABASE={settings.AZURE_SQL_DATABASE};"
            f"UID={settings.AZURE_SQL_USER};"
            f"PWD={settings.AZURE_SQL_PASSWORD};"
            f"Connection Timeout={settings.AZURE_CONNECT_TIMEOUT};"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
        )
        return pyodbc.connect(conn_str)
    except Exception as e:
        print("❌ Database Connection Error")
        print(e)
        raise


# ==============================================================================
# 5. BUILD QUERY & GET DATA FROM DATABASE
# ==============================================================================
def build_query(filters: Dict, period_start: Optional[str], period_end: Optional[str]):
    """
    Build dynamic SQL query based on filters
    
    Filter names từ app.js được map như sau:
      - "Redmine Infra" -> column "redmine_infra"
      - "Redmine Server" -> column "redmine_server"
      - "Redmine Instance" -> column "redmine_instance"
      - "Project Identifier" -> column "project_identifier"
      - "Filter 1 (Vw Bug Report By Testplan)" -> column "filter_1"
      ...
    """
    # SELECT 3 cột chính từ EAV model
    sql = f"""
        SELECT 
            date, 
            Metric_Name, 
            Metric_Value 
        FROM [{DB_SCHEMA_NAME}].[{DB_VIEW_NAME}]
        WHERE 1=1
            AND date IS NOT NULL
    """
    
    params = []

    # 1. XỬ LÝ PERIOD (DATE RANGE) - Chỉ thêm nếu cả hai date được cung cấp
    if period_start and period_end:
        sql += " AND date BETWEEN ? AND ?"
        params.append(period_start)
        params.append(period_end)
        print(f"   📅 Period filter: {period_start} to {period_end}")
    else:
        print(f"   📅 Period filter: NONE (will fetch all available data)")

    # 2. XỬ LÝ FILTERS
    print(f"   🔍 Processing {len(filters)} filters:")
    for filter_name, filter_value in filters.items():
        # Tìm mapping từ filter name (từ dashboard) sang column name (trong DB)
        db_column = FILTER_COLUMN_MAPPING.get(filter_name)
        
        if not db_column:
            # Nếu không có mapping, skip
            print(f"      ⊘ {filter_name}: NO MAPPING (skipped)")
            continue
        
        # Bỏ qua nếu value là (All) hoặc rỗng
        if not filter_value or filter_value == "(All)" or filter_value == ["(All)"] or filter_value == []:
            print(f"      ⊘ {filter_name}: ALL VALUES (skipped)")
            continue
        
        # Xử lý list values
        if isinstance(filter_value, list):
            clean_values = [v for v in filter_value if v and v != "(All)"]
            if clean_values:
                placeholders = ', '.join(['?' for _ in clean_values])
                sql += f" AND [{db_column}] IN ({placeholders})"
                params.extend(clean_values)
                print(f"      ✓ {filter_name} IN ({', '.join(clean_values)})")
        
        # Xử lý string value
        elif isinstance(filter_value, str):
            sql += f" AND [{db_column}] = ?"
            params.append(filter_value)
            print(f"      ✓ {filter_name} = '{filter_value}'")
    
    print(f"\n   ✅ Final SQL:\n{sql}")
    print(f"   ✅ Params: {params}\n")
    
    return sql, params


def get_data_from_db(filters: Dict, period_start: Optional[str], period_end: Optional[str]):
    """Query database and return raw data as DataFrame"""
    print("\n⚙️ STEP 1: BUILD QUERY")
    print("-" * 80)
    sql, params = build_query(filters, period_start, period_end)

    print("\n🔌 STEP 2: CONNECT & QUERY DATABASE")
    print("-" * 80)
    try:
        conn = get_db_connection()
        print("   ✓ Connected")
        
        df = pd.read_sql(sql, conn, params=params)
        conn.close()
        print(f"   ✓ Query returned {len(df)} rows")
        
        if len(df) > 0:
            print(f"   ✓ Date range in raw data: {df['date'].min()} to {df['date'].max()}")
            print(f"   ✓ Unique Metric_Names: {df['Metric_Name'].unique().tolist()}")
            print(f"   ✓ Sample data:\n{df.head(10)}")
        
        return df
        
    except Exception as db_err:
        print(f"   ❌ Database error: {str(db_err)}")
        raise



# ==============================================================================
# 6. PROCESS DATA & BUILD PAYLOAD
# ==============================================================================
def process_data_to_metrics(df: pd.DataFrame):
    """
    Transform raw EAV data to wide format metrics
    Returns list of records with date and metrics
    """
    if df.empty:
        print("\n⚠️ STEP 3: PROCESS DATA")
        print("-" * 80)
        print("   ⊘ No data returned from query")
        return []
    
    print("\n📊 STEP 3: PROCESS DATA (EAV → Wide Format)")
    print("-" * 80)
    
    # 1. Clean & standardize dates
    print("   Step 3.1: Standardize dates...")
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    date_min = df['date'].min()
    date_max = df['date'].max()
    print(f"      ✓ Date range: {date_min} to {date_max}")
    print(f"      ✓ Total unique dates: {df['date'].nunique()}")

    # 2. Filter valid metrics
    print("   Step 3.2: Filter valid metrics...")
    valid_metrics = list(METRIC_VALUE_MAPPING.keys())
    print(f"      Expected metrics: {valid_metrics}")
    metrics_in_data = df['Metric_Name'].unique().tolist()
    print(f"      Metrics in data: {metrics_in_data}")
    
    df_before = len(df)
    df = df[df['Metric_Name'].isin(valid_metrics)]
    df_after = len(df)
    print(f"      ✓ Filtered: {df_before} → {df_after} rows")
    
    if df_after == 0:
        print("      ⚠️ WARNING: No valid metrics found after filtering!")
        return []
    
    # 3. Map metric names (if needed)
    print("   Step 3.3: Map metric names...")
    df['Metric_Name'] = df['Metric_Name'].map(METRIC_VALUE_MAPPING)
    print(f"      ✓ Mapped")

    # 4. Convert Metric_Value to numeric
    print("   Step 3.4: Convert Metric_Value to numeric...")
    df['Metric_Value'] = pd.to_numeric(df['Metric_Value'], errors='coerce')
    print(f"      ✓ Converted")

    # 5. Pivot: EAV to Wide format
    print("   Step 3.5: Pivot data (EAV → Wide)...")
    df_pivot = df.pivot_table(
        index='date',
        columns='Metric_Name',
        values='Metric_Value',
        aggfunc='first'
    ).reset_index()
    print(f"      ✓ Pivoted: {len(df_pivot)} date rows × {len(df_pivot.columns)-1} metrics")
    print(f"      ✓ Columns: {df_pivot.columns.tolist()}")

    # 6. Fill NaN & Convert to int/float
    print("   Step 3.6: Clean & convert types...")
    df_pivot = df_pivot.fillna(0)
    # Convert numeric columns to numeric type
    for col in df_pivot.columns:
        if col != 'date':
            df_pivot[col] = pd.to_numeric(df_pivot[col], errors='coerce').fillna(0).astype(int)
    print(f"      ✓ Ready for output")
    print(f"      ✓ Data types:\n{df_pivot.dtypes}")

    # 7. Sort by date and convert to list of dicts
    df_pivot = df_pivot.sort_values('date').reset_index(drop=True)
    metrics_data = df_pivot.to_dict(orient='records')
    print(f"      ✓ Converted to {len(metrics_data)} records")
    if len(metrics_data) > 0:
        print(f"      ✓ First record: {metrics_data[0]}")
        print(f"      ✓ Last record: {metrics_data[-1]}")
    
    return metrics_data


def normalize_filter_names(filters: Dict):
    """
    Map filter display names to short names for JSON payload
    Example: "Filter 1 (Vw Bug Report By Testplan)" -> "filter_1"
    """
    normalized = {}
    for filter_name, filter_value in filters.items():
        # Get short display name from mapping, or keep original if not found
        short_name = FILTER_DISPLAY_NAME_MAPPING.get(filter_name, filter_name)
        normalized[short_name] = filter_value
    return normalized


def normalize_filters_for_backend(filters: Dict):
    """
    Ensure backend-required filters exist and values are lists.
    Remove (All) placeholders and normalize empty values to empty list.
    """
    required_keys = [
        "redmine_infra",
        "redmine_server",
        "redmine_instance",
        "project_identifier",
        "project_name",
    ]

    normalized = {}
    for key, value in filters.items():
        if value is None:
            normalized[key] = []
            continue

        if isinstance(value, list):
            clean_values = [v for v in value if v and v != "(All)"]
            normalized[key] = clean_values
        elif isinstance(value, str):
            normalized[key] = [value] if value and value != "(All)" else []
        else:
            normalized[key] = []

    for key in required_keys:
        normalized.setdefault(key, [])

    return normalized


def build_backend_payload(request_data: RequestPayload, metrics_data: List[Dict], actual_period: Dict):
    """
    Build JSON payload to send to Backend API
    """
    print("\n📦 STEP 4: BUILD PAYLOAD FOR BACKEND API")
    print("-" * 80)
    
    # Generate request metadata
    request_id = generate_request_id()
    timestamp = get_iso_timestamp()
    
    # Normalize filter names
    normalized_filters = normalize_filter_names(request_data.filters)
    normalized_filters = normalize_filters_for_backend(normalized_filters)
    
    # Build final payload
    payload = {
        "request_meta": {
            "request_id": request_id,
            "timestamp": timestamp,
            "mode_type": request_data.mode_type
        },
        "period": actual_period,
        "filters": normalized_filters,
        "metrics_data": metrics_data
    }
    
    # Add user_question if exists (for AI Assistant mode)
    if request_data.user_question:
        payload["user_question"] = request_data.user_question
    
    print(f"   ✓ Request ID: {request_id}")
    print(f"   ✓ Mode: {request_data.mode_type}")
    print(f"   ✓ Period: {actual_period}")
    print(f"   ✓ Filters: {list(normalized_filters.keys())}")
    print(f"   ✓ Metrics records: {len(metrics_data)}")
    print("="*80 + "\n")
    
    return payload


async def call_backend_api(payload: Dict, endpoint: str):
    """
    Call Backend API at port 7071 and get response
    """
    print("\n🚀 STEP 5: CALL BACKEND API")
    print("-" * 80)
    print(f"   Endpoint: {endpoint}")

    headers = {
        "Content-Type": "application/json",
        "x-api-key": BACKEND_API_KEY,
        "Authorization": f"Bearer {BACKEND_JWT_TOKEN}",
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                endpoint,
                json=payload,
                headers=headers,
            )
            
            print(f"   ✓ Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✓ Response received")
                print("="*80 + "\n")
                return result
            else:
                error_text = response.text
                print(f"   ❌ Backend API error: {error_text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Backend API error: {error_text}"
                )
                
        except httpx.TimeoutException:
            print(f"   ❌ Backend API timeout")
            raise HTTPException(status_code=504, detail="Backend API timeout")
        except httpx.RequestError as e:
            print(f"   ❌ Backend API connection error: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail=f"Cannot connect to Backend API: {str(e)}"
            )



# ==============================================================================
# 7. API ENDPOINTS
# ==============================================================================

@app.post('/ask-ai')
async def ask_ai(request_data: RequestPayload):
    """
    Main endpoint: 
    1. Receive filters from Tableau Extension
    2. Query database with filters as WHERE conditions
    3. Build JSON payload with data
    4. Send to Backend API (port 7071)
    5. Return Backend API response to frontend
    """
    try:
        print("\n" + "="*80)
        print("📥 REQUEST FROM TABLEAU EXTENSION")
        print("="*80)
        print(f"Mode: {request_data.mode_type}")
        print(f"Period: {request_data.period}")
        print(f"Filters: {list(request_data.filters.keys())}")
        if request_data.user_question:
            print(f"User Question: {request_data.user_question}")
        
        # Extract period
        p_start = request_data.period.start_date if request_data.period else None
        p_end = request_data.period.end_date if request_data.period else None

        # ===== STEP 1 & 2: QUERY DATABASE =====
        df = get_data_from_db(request_data.filters, p_start, p_end)

        # ===== STEP 3: PROCESS DATA =====
        metrics_data = process_data_to_metrics(df)

        if not metrics_data:
            return JSONResponse(
                content={
                    "answer": "<div style='background:#fff3cd; padding:12px; border-left:4px solid #ffc107; border-radius:4px;'>No metrics data found for the selected filters.</div>",
                    "data": {"metrics_records": 0}
                },
                status_code=200
            )
        
        # Calculate actual period from data
        actual_period = {
            "start_date": request_data.period.start_date if request_data.period else None,
            "end_date": request_data.period.end_date if request_data.period else None
        }
        
        if metrics_data and len(metrics_data) > 0:
            dates = [record.get('date') for record in metrics_data if record.get('date')]
            if dates:
                dates_sorted = sorted(dates)
                actual_period['start_date'] = dates_sorted[0]
                actual_period['end_date'] = dates_sorted[-1]

        # ===== STEP 4: BUILD PAYLOAD =====
        backend_payload = build_backend_payload(request_data, metrics_data, actual_period)

        # Determine backend endpoint based on mode
        mode_type = request_data.mode_type or (request_data.request_meta.mode_type if request_data.request_meta else None)
        if mode_type == "AI Assistant":
            backend_endpoint = ASSISTANT_API_ENDPOINT
        else:
            backend_endpoint = ANALYSIS_API_ENDPOINT
        
        # ===== STEP 5: CALL BACKEND API (or return payload in DEBUG mode) =====
        # Code debug for: DEBUG_MODE check (disabled - always calling backend API now)
        if DEBUG_MODE:
            # Code debug for: Build debug response with payload inspection data (disabled)
            pass
        else:
            # Production mode - call real backend API
            try:
                backend_response = await call_backend_api(backend_payload, backend_endpoint)
                
                # ===== STEP 6: RETURN RESPONSE =====
                # Code debug for: Print log when response received (optional - uncomment to debug)
                # print("\n📤 SENDING RESPONSE TO FRONTEND")
                # print("-" * 80)
                # print("   ✓ Response from Backend API received and forwarded")
                # print("="*80 + "\n")
                
                # Normalize backend response to frontend format
                backend_message = backend_response.get("message") if isinstance(backend_response, dict) else None
                normalized_response = {
                    "answer": f"<div style='white-space:pre-wrap;'>{backend_message or ''}</div>",
                    "data": backend_response,
                }

                # Return normalized response to frontend
                return JSONResponse(content=normalized_response)
                
            except HTTPException as he:
                # Backend API error - return detailed error message
                print(f"\n❌ Backend API Error: {he.detail}")
                
                # Code debug for: Build error response when backend API fails (commented debug_info)
                error_response = {
                    "answer": f"""
                    <div style="background:#f8d7da; padding:15px; border-left:4px solid #dc3545; margin-bottom:15px; border-radius:4px;">
                        <h4 style="margin:0 0 10px 0; color:#721c24;">❌ Backend API Error</h4>
                        <p style="margin:5px 0; color:#721c24;">
                            <strong>Cannot connect to Backend API</strong><br>
                            Endpoint: <code>{backend_endpoint}</code><br>
                            Error: {he.detail}
                        </p>
                        <hr style="border-color:#f5c6cb; margin:10px 0;">
                        <p style="margin:5px 0; font-size:0.9em; color:#721c24;">
                            💡 <strong>Solutions:</strong><br>
                            1. Make sure Backend API is running on port 7071<br>
                            2. Check that JWT token and API key are correct
                        </p>
                    </div>
                    """,
                    "error": str(he.detail),
                    # Code debug for: Omit payload_sent and backend_endpoint from error response (commented out for cleaner output)
                    # "payload_sent": backend_payload,
                    # "backend_endpoint": backend_endpoint
                }
                
                # Code debug for: Return error response with status 200 so frontend can display user-friendly message
                return JSONResponse(content=error_response, status_code=200)

    except HTTPException as he:
        # Re-raise HTTP exceptions from backend API call
        raise he
    except Exception as e:
        # Code debug for: Catch-all exception handler (optional - print traceback uncomment to debug)
        # import traceback
        # error_msg = traceback.format_exc()
        # print(f"\n❌ ERROR OCCURRED:")
        # print(error_msg)
        # print("="*80 + "\n")
        
        # Code debug for: Return system error response with error message (without full traceback in production)
        return JSONResponse(
            status_code=500,
            content={
                "answer": f"<div style='color:#c62828; background:#ffebee; padding:12px; border-left:4px solid #c62828; border-radius:4px;'><h5 style='margin:0;'>❌ Error</h5><p style='margin:8px 0;'>{str(e)}</p></div>",
                "error": str(e)
            }
        )


# ==============================================================================
# 8. SERVE STATIC FILES
# ==============================================================================

@app.get('/')
async def index():
    """Serve index.html"""
    static_folder = os.path.dirname(os.path.abspath(__file__))
    return FileResponse(os.path.join(static_folder, 'index.html'))

@app.get('/{path:path}')
async def serve_static(path: str):
    """Serve static files (CSS, JS, etc.)"""
    static_folder = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(static_folder, path)
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    else:
        raise HTTPException(status_code=404, detail="File not found")


# ==============================================================================
# 9. RUN SERVER
# ==============================================================================

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)