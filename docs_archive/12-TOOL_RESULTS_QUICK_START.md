# Tool Results Storage - Quick Start Guide

**Quick Implementation Guide for Tool Result Storage and Display**

---

## ⚡ What Changed

### New Backend Files
```
/backend/app/services/tool_result_service.py (400+ lines)
  - Process and store tool scan results
  - Extract findings to database
  - Aggregate statistics
```

### Enhanced Files
```
/backend/app/api/v1_tools.py (enhanced)
  + GET /api/v1/tools/task/{task_id}/results
  + POST /api/v1/tools/task/{task_id}/execute-and-store
```

### New Frontend Files
```
/frontend/src/pages/tasks/ToolResultsViewer.tsx (400+ lines)
  - Display tool results
  - Show statistics
  - Export raw JSON
```

---

## 🚀 Usage Examples

### 1. Execute Tool and Store Results (Recommended)

```bash
# Execute FScan port scan and store results
curl -X POST "http://localhost:8000/api/v1/tools/task/5/execute-and-store" \
  -H "Authorization: Bearer $TOKEN" \
  -d "tool_name=fscan&target=192.168.1.100"

# Execute Nuclei vulnerability scan and store results
curl -X POST "http://localhost:8000/api/v1/tools/task/5/execute-and-store" \
  -H "Authorization: Bearer $TOKEN" \
  -d "tool_name=nuclei&target=http://example.com"
```

Response:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "execution": { /* tool output */ },
    "storage": {
      "status": "success",
      "findings": 8,
      "vulnerabilities": 2,
      "ports": 8,
      "task_result_id": 42
    },
    "task_id": 5
  }
}
```

### 2. View Stored Results

```bash
# Get all results for task
curl "http://localhost:8000/api/v1/tools/task/5/results" \
  -H "Authorization: Bearer $TOKEN" | jq .

# Filter by tool
curl "http://localhost:8000/api/v1/tools/task/5/results?tool_name=fscan" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

### 3. Use Frontend Component

```typescript
import ToolResultsViewer from '@/pages/tasks/ToolResultsViewer';

export function TaskDetail() {
  return <ToolResultsViewer taskId={5} />;
}
```

---

## 📊 What Gets Stored

### Raw Data
```
TaskResult table:
- Raw tool output (JSON)
- Tool name
- Timestamp
- Task reference
```

### Extracted Findings
```
Vulnerability table:
- Port findings (FScan) → Vulnerability with severity "info"
- Vulnerabilities (Nuclei) → Vulnerability with extracted severity
- PoC results (Afrog) → Vulnerability with details
- Directories (DirSearch) → Vulnerability with severity "info"
```

---

## 🔍 Frontend Features

### Overview Tab
- Total tools executed
- Total findings
- Vulnerabilities count
- Ports count
- Severity distribution
- Tools used list

### Results Tab
- Tool-specific formatting
- Sortable/filterable tables
- Color-coded severity
- Pagination

### Raw Data Tab
- Full JSON output
- Download button
- Syntax highlighting

---

## 📈 Example Response

### Get Task Results
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": 5,
    "task_name": "Network Scan",
    "task_status": "completed",
    "results": [
      {
        "id": 1,
        "tool": "fscan",
        "data": {
          "tool": "fscan",
          "target": "192.168.1.100",
          "status": "success",
          "ports_found": 8,
          "results": [
            {"ip": "192.168.1.100", "port": 22, "service": "ssh", "version": "OpenSSH"},
            {"ip": "192.168.1.100", "port": 80, "service": "http", "version": "Apache"}
          ]
        },
        "created_at": "2025-11-12T10:30:45"
      },
      {
        "id": 2,
        "tool": "nuclei",
        "data": {
          "tool": "nuclei",
          "target": "http://192.168.1.100",
          "status": "success",
          "vulnerabilities_found": 2,
          "results": [
            {"id": "cve-2021-41773", "name": "Apache RCE", "severity": "critical"}
          ]
        },
        "created_at": "2025-11-12T10:35:20"
      }
    ],
    "statistics": {
      "task_id": 5,
      "task_name": "Network Scan",
      "task_status": "completed",
      "tools_executed": ["fscan", "nuclei"],
      "tools_count": 2,
      "total_ports": 8,
      "total_vulnerabilities": 2,
      "total_directories": 0,
      "total_findings": 10,
      "severity_distribution": {
        "critical": 1,
        "high": 0,
        "medium": 1,
        "low": 0,
        "info": 8
      }
    }
  }
}
```

---

## ✨ Key Features

✅ **Automatic Storage** - Execute tool → Results stored automatically
✅ **Data Extraction** - Findings extracted to vulnerability table
✅ **Statistics** - Automatic aggregation of findings
✅ **Multiple Tools** - Support for all 5 integrated tools
✅ **Frontend Display** - Beautiful UI for viewing results
✅ **Export** - Download raw JSON data
✅ **Filtering** - Filter results by tool
✅ **Pagination** - Handle large result sets

---

## 🔄 Complete Workflow

```
1. Create Task
   POST /api/v1/tasks
   → task_id = 5

2. Execute Tool and Store
   POST /api/v1/tools/task/5/execute-and-store?tool_name=fscan&target=192.168.1.100
   → Results stored in database

3. View Results (API)
   GET /api/v1/tools/task/5/results
   → Get all stored results and statistics

4. View Results (Frontend)
   <ToolResultsViewer taskId={5} />
   → Beautiful UI with tabs and charts

5. Generate Report
   GET /api/v1/reports/task/5?format=html
   → Report includes tool findings
```

---

## 🛠️ Implementation Checklist

- [x] Backend service created
- [x] API endpoints added
- [x] Database storage working
- [x] Result processing implemented
- [x] Frontend component created
- [x] Statistics aggregation
- [x] Error handling
- [x] Documentation

**Ready to use immediately!**

---

## 📋 API Endpoints Summary

| Endpoint | Method | Purpose | Example |
|----------|--------|---------|---------|
| `/tools/task/{id}/results` | GET | Get stored results | `curl "http://localhost:8000/api/v1/tools/task/5/results"` |
| `/tools/task/{id}/execute-and-store` | POST | Execute & store | `curl -X POST "http://localhost:8000/api/v1/tools/task/5/execute-and-store?tool_name=fscan&target=192.168.1.100"` |

---

## 🎯 Next Steps

1. **Test it:** Execute a tool on a task and view results
2. **Integrate:** Add ToolResultsViewer to task detail page
3. **Customize:** Modify result processing if needed
4. **Scale:** Monitor performance with large result sets

---

**That's it! You can now execute tools and view results in the database and frontend!**

See **TOOL_RESULTS_STORAGE.md** for comprehensive documentation.
