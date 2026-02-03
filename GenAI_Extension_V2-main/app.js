// --- CẤU HÌNH ---
const MAIN_SHEET_NAME = "Line_Chart"; 

// --- KHỞI TẠO ---

// Tab switching
document.querySelectorAll(".tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));

    tab.classList.add("active");
    document.getElementById(tab.dataset.tab).classList.add("active");
  });
});
let dashboard;
tableau.extensions.initializeAsync().then(() => {
    dashboard = tableau.extensions.dashboardContent.dashboard;
    //console.log("✅ Extension initialized");
    // 1. Gắn sự kiện cho nút ANALYZE (Report)
    const analyzeBtn = document.getElementById("analyzeBtn");
    if(analyzeBtn) {
        analyzeBtn.addEventListener("click", () => handleProcess("Analyze_Data"));
    }
    // 2. Gắn sự kiện cho nút SEND (Chat AI)
    const sendBtn = document.getElementById("sendBtn");
    const chatInput = document.getElementById("chatInput");
    const charCount = document.getElementById("charCount");
    
    if(sendBtn) {
        sendBtn.addEventListener("click", () => handleProcess("AI_Assistant"));
    }
    
    if(chatInput) {
        // Enable/disable send button based on input
        chatInput.addEventListener("input", (e) => {
            const text = e.target.value.trim();
            const charCountText = `${text.length} / 500`;
            
            if(charCount) charCount.textContent = charCountText;
            if(sendBtn) sendBtn.disabled = text.length === 0;
        });
        
        // Allow Shift+Enter to send
        chatInput.addEventListener("keydown", (e) => {
            if(e.key === "Enter" && e.shiftKey && !sendBtn.disabled) {
                handleProcess("AI_Assistant");
            }
        });
    }
});

// --- HÀM XỬ LÝ CHUNG (Nhận tham số modeType) ---
async function handleProcess(modeType) {
    // Xác định vùng hiển thị kết quả dựa trên Mode
    const isChatMode = (modeType === "AI_Assistant");
    
    // Lấy các element UI tương ứng
    const statusText = document.getElementById("statusText"); // Text trạng thái chung
    
    // Nếu là Chat Mode thì hiển thị kết quả vào ô chat, ngược lại vào ô Analyze
    const resultContainer = isChatMode 
        ? document.getElementById("chatResult") 
        : document.getElementById("analyzeResult");

    // Lấy câu hỏi của User (Chỉ dùng nếu là AI Assistant)
    const userQuestion = isChatMode 
        ? document.getElementById("chatInput").value 
        : "";

    try {
        // Validate chat input for AI Assistant mode
        if(isChatMode && !userQuestion.trim()) {
            throw new Error("Vui lòng nhập câu hỏi trước khi gửi");
        }

        if(statusText) statusText.textContent = `Processing ${modeType}...`;
        if(resultContainer) {
            resultContainer.innerHTML = "⏳ Collecting data & running analysis…";
            resultContainer.classList.remove("empty");
        }

        // --- BƯỚC 1: LẤY DỮ LIỆU DASHBOARD (Dùng chung cho cả 2 mode) ---
        // Code debug for: Log step 1 (commented)
        // console.log("\n" + "=".repeat(80));
        // console.log("🔍 BƯỚC 1: GET FILTERS FROM DASHBOARD");
        // console.log("=".repeat(80));
        
        // 1.1 Lấy Filter thô
        const rawFilters = await getRawFilters();
        // Code debug for: Log raw filters before enrichment (commented)
        // console.log("📥 Raw Filters (Before enrichment):", JSON.stringify(rawFilters, null, 2));

        // 1.2 Cross-check để lấy giá trị thực (Fix lỗi All)
        const finalFilters = await enrichFiltersWithData(rawFilters);
        // Code debug for: Log final filters after enrichment (commented)
        // console.log("✅ Final Filters (After enrichment):", JSON.stringify(finalFilters, null, 2));

        // --- BƯỚC 2: ĐÓNG GÓP PAYLOAD ---
        // Code debug for: Log step 2 (commented)
        // console.log("\n" + "=".repeat(80));
        // console.log("📦 BƯỚC 2: BUILD JSON PAYLOAD");
        // console.log("=".repeat(80));
        
        // Xử lý period: Ban đầu gửi null để backend lấy toàn bộ dữ liệu, 
        // sau đó backend sẽ tính min/max date từ dữ liệu thực tế
        const payload = {
            "request_meta": { 
                "mode_type": modeType === "Analyze_Data" ? "Analyze Report" : "AI Assistant",
                "question": isChatMode ? userQuestion : ""
            },
            "period": {
                "start_date": null,
                "end_date": null
            },
            "filters": finalFilters,
            "mode_type": modeType === "Analyze_Data" ? "Analyze Report" : "AI Assistant"
        };
        
        // Thêm user_question nếu là Chat mode
        if(isChatMode && userQuestion) {
            payload.user_question = userQuestion;
        }

        // Code debug for: Show full payload in console
        // console.log("✅ Payload built successfully:");
        // console.log(JSON.stringify(payload, null, 2));
        
        // Code debug for: Display payload in UI (uncomment to enable)
        // if(resultContainer) {
        //     resultContainer.innerHTML = `
        //         <div style="background:#fff3cd; padding:15px; border-left:4px solid #ffc107; margin-bottom:15px; border-radius:4px;">
        //             <h4 style="margin:0 0 10px 0; color:#856404;">🔍 DEBUG MODE</h4>
        //             <p style="margin:5px 0; color:#856404;">
        //                 <strong>✅ Filters collected successfully!</strong><br>
        //                 <strong>✅ Payload built successfully!</strong>
        //             </p>
        //         </div>
                
        //         <details open style="background:#f8f9fa; padding:15px; border-radius:4px; margin-bottom:15px;">
        //             <summary style="cursor:pointer; font-weight:bold; color:#495057; font-size:16px;">
        //                 📋 Raw Filters (từ Dashboard)
        //             </summary>
        //             <pre style="background:#fff; border:1px solid #dee2e6; padding:12px; overflow-x:auto; font-size:12px; margin-top:10px; border-radius:4px;">${JSON.stringify(rawFilters, null, 2)}</pre>
        //         </details>
                
        //         <details open style="background:#f8f9fa; padding:15px; border-radius:4px; margin-bottom:15px;">
        //             <summary style="cursor:pointer; font-weight:bold; color:#495057; font-size:16px;">
        //                 ✅ Final Filters (sau khi enrich)
        //             </summary>
        //             <pre style="background:#fff; border:1px solid #dee2e6; padding:12px; overflow-x:auto; font-size:12px; margin-top:10px; border-radius:4px;">${JSON.stringify(finalFilters, null, 2)}</pre>
        //         </details>
                
        //         <details open style="background:#e7f5ff; padding:15px; border-radius:4px; border-left:4px solid #0d6efd;">
        //             <summary style="cursor:pointer; font-weight:bold; color:#084298; font-size:16px;">
        //                 📦 JSON PAYLOAD (ready to send)
        //             </summary>
        //             <pre style="background:#fff; border:1px solid #0d6efd; padding:12px; overflow-x:auto; font-size:12px; margin-top:10px; border-radius:4px;">${JSON.stringify(payload, null, 2)}</pre>
        //         </details>
                
        //         <div style="background:#d1ecf1; padding:15px; border-left:4px solid #0dcaf0; margin-top:15px; border-radius:4px;">
        //             <p style="margin:0; color:#055160; font-size:14px;">
        //                 💡 <strong>Next step:</strong> Nhấn nút bên dưới để gửi payload này đến Backend API
        //             </p>
        //         </div>
        //     `;
        // }
        
        // Code debug for: Log filters summary
        // const filterCount = Object.keys(finalFilters).length;
        // console.log(`📊 Summary: ${filterCount} filters collected`);
        // console.log("=".repeat(80) + "\n");
        
        if(statusText) statusText.textContent = "Sending to backend...";
        
        // Code debug for: Stop here to inspect payload (uncomment return below)
        // return; // <-- UNCOMMENT to stop before sending to backend
        
        // --- BƯỚC 3: GỬI SANG BACKEND ---
        // Code debug for: GỬI SANG BACKEND (Uncomment console logs to enable)
        // console.log("\n" + "=".repeat(80));
        // console.log("🚀 BƯỚC 3: SENDING TO BACKEND API");
        // console.log("=".repeat(80));
        // console.log(`📤 Sending payload [${modeType}]:`, payload);
        // console.log("🚀 Gửi request tới /ask-ai...");
        const backendResponse = await sendToBackend(payload);
        
        // console.log("📥 Response từ backend:", backendResponse);
        
        // Code debug for: Display response in debug panel (uncomment to enable)
        // const debugPanel = document.getElementById("debugPanel");
        // if(debugPanel) {
        //     debugPanel.textContent = JSON.stringify(backendResponse.data || backendResponse, null, 2);
        // }
        
        // --- BƯỚC 4: HIỂN THỊ KẾT QUẢ ---
        let displayHtml = `
            <div style="text-align:left;">
                <div style="background:#e3f2fd; padding:10px; margin-bottom:10px; border-left:4px solid #2196F3;">
                    ${backendResponse.answer || ""}
                </div>
        `;
        
        // Code debug for: Display full JSON response in collapsible panel (uncomment to enable)
        // if(backendResponse.data) {
        //     displayHtml += `
        //         <details open style="background:#f5f5f5; padding:10px; margin-top:10px; border-radius:4px;">
        //             <summary style="cursor:pointer; font-weight:bold; color:#333;">
        //                 📋 JSON Response (DEBUG)
        //             </summary>
        //             <pre style="background:#fff; border:1px solid #ddd; padding:10px; overflow-x:auto; font-size:11px; margin-top:8px;">
        // ${JSON.stringify(backendResponse.data, null, 2)}
        //             </pre>
        //         </details>
        //     `;
        // }
        
        displayHtml += `</div>`;
        
        if(resultContainer) resultContainer.innerHTML = displayHtml;
        if(statusText) statusText.textContent = "✅ Completed";
        
        // Clear chat input after successful send
        if(isChatMode) {
            const chatInput = document.getElementById("chatInput");
            if(chatInput) {
                chatInput.value = "";
                const charCount = document.getElementById("charCount");
                if(charCount) charCount.textContent = "0 / 500";
                const sendBtn = document.getElementById("sendBtn");
                if(sendBtn) sendBtn.disabled = true;
            }
        }

    } catch (err) {
        console.error(err);
        if(resultContainer) resultContainer.innerHTML = `<span style="color:red">❌ Lỗi: ${err.message}</span>`;
        if(statusText) statusText.textContent = "Failed";
    }
}

// --- HÀM 1: LẤY FILTER THÔ ---
async function getRawFilters() {
    // Code debug for: Log sheet lookup (commented)
    // console.log(`   🔍 Looking for sheet: "${MAIN_SHEET_NAME}"`);
    const sheet = dashboard.worksheets.find(w => w.name === MAIN_SHEET_NAME);
    if (!sheet) {
        console.error(`   ❌ Sheet not found: ${MAIN_SHEET_NAME}`);
        // Code debug for: Log available sheets (commented)
        // console.log(`   Available sheets:`, dashboard.worksheets.map(w => w.name));
        throw new Error(`Không tìm thấy sheet: ${MAIN_SHEET_NAME}`);
    }
    // Code debug for: Log when sheet found (commented)
    // console.log(`   ✅ Sheet found: "${sheet.name}"`);
    
    const filters = await sheet.getFiltersAsync();
    // Code debug for: Log total filters count (commented)
    // console.log(`   📊 Total filters found: ${filters.length}`);
    
    const filterMap = {};
    
    // DANH SÁCH CÁC FILTER MUỐN BỎ QUA (BLACKLIST)
    // Bạn có thể thêm bất kỳ filter nào không muốn gửi đi vào đây
    const IGNORED_FILTERS = [
        "Measure Names", 
        "Metric Name Set", 
        "Filter_Weekend" // <--- Thêm cái này vào
    ];

    filters.forEach(f => {
        // Code debug for: Log filter processing details (commented)
        // console.log(`   🔎 Processing filter: "${f.fieldName}"`);
        // console.log(`      - Type: ${f.filterType}`);
        // console.log(`      - isAllSelected: ${f.isAllSelected}`);
        
        // Kiểm tra xem tên filter có nằm trong danh sách bị loại trừ không
        if (IGNORED_FILTERS.includes(f.fieldName)) {
            // Code debug for: Log ignored filter (commented)
            // console.log(`      ⊘ IGNORED (in blacklist)`);
            return;
        }
        
        if (f.isAllSelected) {
            filterMap[f.fieldName] = ["(All)"];
            // Code debug for: Log collected all values (commented)
            // console.log(`      ✓ Collected: ["(All)"]`);
        } else {
            const values = f.appliedValues.map(v => v.formattedValue);
            filterMap[f.fieldName] = values;
            // Code debug for: Log collected specific values (commented)
            // console.log(`      ✓ Collected: [${values.join(", ")}]`);
        }
    });
    
    // Code debug for: Log final filters collected count (commented)
    // console.log(`   ✅ Filters collected: ${Object.keys(filterMap).length} filters`);
    return filterMap;
}

// --- HÀM 2: CROSS-CHECK DỮ LIỆU ---
async function enrichFiltersWithData(currentFilters) {
    // Code debug for: Log enrichment start (commented)
    // console.log(`   🔄 Enriching filters with actual data...`);
    
    const sheet = dashboard.worksheets.find(w => w.name === MAIN_SHEET_NAME);
    const summary = await sheet.getSummaryDataAsync({ maxRows: 0 }); 
    const data = summary.data;
    const columns = summary.columns;

    // Code debug for: Log sheet structure info (commented)
    // console.log(`   📊 Sheet has ${columns.length} columns and ${data.length} rows`);
    // console.log(`   📋 Columns:`, columns.map(c => c.fieldName));

    for (const [filterName, filterValue] of Object.entries(currentFilters)) {
        if (filterValue[0] === "(All)") {
            // Code debug for: Log filter enrichment start (commented)
            // console.log(`   🔍 Enriching "${filterName}" (currently set to All)...`);
            
            const colIndex = columns.findIndex(c => {
                const dbName = c.fieldName.replace(/[\[\]]/g, ""); 
                const fName = filterName.replace(/[\[\]]/g, "");
                return dbName === fName || dbName.includes(fName); 
            });
            
            if (colIndex !== -1 && data.length > 0) {
                // Code debug for: Log column match (commented)
                // console.log(`      ✓ Found matching column at index ${colIndex}: "${columns[colIndex].fieldName}"`);
                
                const uniqueValues = new Set();
                const limit = Math.min(data.length, 500); 
                for (let i = 0; i < limit; i++) {
                    uniqueValues.add(data[i][colIndex].formattedValue);
                }

                // Code debug for: Log unique values found (commented)
                // console.log(`      📊 Found ${uniqueValues.size} unique values`);
                
                if (uniqueValues.size === 1) {
                    currentFilters[filterName] = Array.from(uniqueValues);
                    // Code debug for: Log single value enrichment (commented)
                    // console.log(`      ✅ Single value found: [${Array.from(uniqueValues)[0]}]`);
                } else if (uniqueValues.size > 1 && uniqueValues.size < 10) {
                    currentFilters[filterName] = Array.from(uniqueValues);
                    // Code debug for: Log multiple values enrichment (commented)
                    // console.log(`      ✅ Multiple values (${uniqueValues.size}): [${Array.from(uniqueValues).join(", ")}]`);
                } else {
                    // Code debug for: Log too many values warning (commented)
                    // console.log(`      ⊘ Too many values (${uniqueValues.size}), keeping as "(All)"`);
                }
            } else {
                // Code debug for: Log column not found (commented)
                // console.log(`      ⊘ Column not found in data or no data available`);
            }
        } else {
            // Code debug for: Log filter already has values (commented)
            // console.log(`   ⊘ "${filterName}" already has specific values, skipping enrichment`);
        }
    }
    
    // Code debug for: Log enrichment completion (commented)
    // console.log(`   ✅ Enrichment complete`);
    return currentFilters;
}

// Hàm gửi backend
async function sendToBackend(payload) {
    try {
        // Code debug for: Log fetch start (commented)
        // console.log("🔌 Fetching /ask-ai...");
        const res = await fetch("http://localhost:8000/ask-ai", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        
        // Code debug for: Log response status (commented)
        // console.log(`   Response status: ${res.status} ${res.statusText}`);
        
        if (!res.ok) {
            const errorData = await res.json();
            throw new Error(errorData.error || `HTTP ${res.status}: ${res.statusText}`);
        }
        
        const data = await res.json();
        // Code debug for: Log response received (commented)
        // console.log("✅ Got response:", data);
        return data;
    } catch (err) {
        console.error("❌ Backend error:", err);
        throw err;
    }
}
