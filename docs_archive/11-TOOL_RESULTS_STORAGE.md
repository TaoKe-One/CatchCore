# Tool Results Storage and Display Guide

**Date:** November 12, 2025
**Feature:** Tool scan results database storage and frontend display
**Status:** ✅ Ready to use

---

## 📋 Overview

CatchCore now supports automatic storage of scan results from all 5 integrated tools (Afrog, DDDD, FScan, Nuclei, DirSearch) directly into the database, with comprehensive frontend display capabilities.

---

## 🏗️ Architecture

### Database Schema

```
Tasks
├── TaskResult (new storage)
│   ├── id (PK)
│   ├── task_id (FK)
│   ├── result_type (e.g., "tool_fscan")
│   ├── result_data (JSON)
│   └── created_at
│
└── Vulnerability (existing)
    ├── id (PK)
    ├── asset_id (FK)
    ├── title
    ├── severity
    ├── status
    └── discovered_at
```

### Data Flow

```
Tool Execution
    ↓
Tool Integration Service
    ↓
Tool Result Service (Parse & Extract)
    ↓
Database Storage
    ├── TaskResult (Raw)
    └── Vulnerability (Extracted findings)
    ↓
API Retrieval
    ↓
Frontend Display
```

---

## 🔧 Components Created

### 1. Backend Service: `ToolResultService`

**File:** `/backend/app/services/tool_result_service.py` (400+ lines)

**Key Methods:**

```python
# Main method to process and store results
process_and_store_result(
    db: AsyncSession,
    task_id: int,
    tool_name: str,
    scan_result: Dict[str, Any],
) -> Dict[str, Any]

# Get stored results for a task
get_tool_results(
    db: AsyncSession,
    task_id: int,
    tool_name: Optional[str] = None,
) -> List[Dict[str, Any]]

# Get task statistics
get_task_statistics(
    db: AsyncSession,
    task_id: int,
) -> Dict[str, Any]

# Tool-specific processing methods
_process_fscan_results()  # Port scanning
_process_nuclei_results()  # Vulnerability scanning
_process_afrog_results()   # PoC execution
_process_dddd_results()    # Advanced scanning
_process_dirsearch_results()  # Directory enumeration
```

### 2. API Endpoints

**File:** `/backend/app/api/v1_tools.py` (enhanced)

#### New Endpoints:

**A. Get Tool Results for Task**
```
GET /api/v1/tools/task/{task_id}/results
```

Parameters:
- `task_id` (path): Task ID
- `tool_name` (query, optional): Filter by tool (afrog, dddd, fscan, nuclei, dirsearch)

Response:
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
        "id": 12,
        "tool": "fscan",
        "data": { /* raw tool output */ },
        "created_at": "2025-11-12T10:30:45"
      }
    ],
    "statistics": {
      "total_findings": 15,
      "total_vulnerabilities": 5,
      "total_ports": 8,
      "severity_distribution": { /* ... */ }
    }
  }
}
```

**B. Execute Tool and Store Results**
```
POST /api/v1/tools/task/{task_id}/execute-and-store
```

Parameters:
- `task_id` (path): Task ID to associate with results
- `tool_name` (query): Tool to execute
- `target` (query): Target address
- `options` (query, optional): Tool-specific options

Example:
```bash
curl -X POST "http://localhost:8000/api/v1/tools/task/5/execute-and-store?tool_name=fscan&target=192.168.1.100" \
  -H "Authorization: Bearer $TOKEN"
```

Response:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "execution": { /* tool execution result */ },
    "storage": {
      "status": "success",
      "findings": 8,
      "vulnerabilities": 0,
      "ports": 8
    },
    "task_id": 5
  }
}
```

### 3. Frontend Component: `ToolResultsViewer`

**File:** `/frontend/src/pages/tasks/ToolResultsViewer.tsx` (400+ lines)

**Features:**
- Overview tab with statistics
- Results tab with tool-specific formatting
- Raw JSON data tab with export
- Severity color coding
- Responsive design for all devices
- Real-time refresh capability

---

## 🚀 Usage Guide

### Scenario 1: Execute Tool and Store Results

```bash
# Execute FScan on target and store results
curl -X POST "http://localhost:8000/api/v1/tools/task/5/execute-and-store" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "fscan",
    "target": "192.168.1.100",
    "options": {
      "threads": 50,
      "timeout": 300
    }
  }'
```

Response includes:
- Tool execution results
- Storage confirmation
- Number of findings extracted

### Scenario 2: View Stored Results

```bash
# Get all results for a task
curl "http://localhost:8000/api/v1/tools/task/5/results" \
  -H "Authorization: Bearer $TOKEN" | jq .

# Get only FScan results
curl "http://localhost:8000/api/v1/tools/task/5/results?tool_name=fscan" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

### Scenario 3: Frontend Integration

In your React component:
```typescript
import ToolResultsViewer from '@/pages/tasks/ToolResultsViewer';

function TaskDetailPage() {
  return (
    <ToolResultsViewer
      taskId={5}
      onRefresh={() => console.log('Refreshed')}
    />
  );
}
```

---

## 📊 Result Processing Details

### FScan Results Processing

**Input:**
```json
{
  "tool": "fscan",
  "ports_found": 8,
  "results": [
    {
      "ip": "192.168.1.100",
      "port": 22,
      "service": "SSH",
      "version": "OpenSSH 7.4"
    }
  ]
}
```

**Output:**
- Creates Asset record if not exists
- Creates Vulnerability record for each port with:
  - Title: "Port 22/SSH"
  - Severity: "info"
  - Description: Service and version information

### Nuclei Results Processing

**Input:**
```json
{
  "tool": "nuclei",
  "vulnerabilities_found": 4,
  "results": [
    {
      "id": "cve-2021-41773",
      "name": "Apache RCE",
      "severity": "critical",
      "matched_at": "http://example.com/cgi-bin/"
    }
  ]
}
```

**Output:**
- Creates Vulnerability record with:
  - Title: Vulnerability name
  - CVE ID: Extracted from result
  - Severity: From tool output
  - Status: "open"

### Afrog Results Processing

Similar to Nuclei, extracts:
- Vulnerability title
- Severity level
- Target URL
- Creates Vulnerability record

### DDDD Results Processing

Processes advanced vulnerability findings:
- Name and description
- Severity information
- Creates Vulnerability records

### DirSearch Results Processing

**Input:**
```json
{
  "tool": "dirsearch",
  "directories_found": 45,
  "results": [
    {
      "path": "/admin",
      "status": 200
    }
  ]
}
```

**Output:**
- Creates Vulnerability record with:
  - Title: "Directory Discovered: /admin"
  - Severity: "info"
  - Description: HTTP status code
  - Status: "open"

---

## 📈 Statistics Aggregation

The system automatically aggregates:

```
Total Findings:
  = Ports + Vulnerabilities + Directories

Severity Distribution:
  - Critical
  - High
  - Medium
  - Low
  - Info

Tools Executed:
  - List of all tools executed for task
  - Timestamp for each execution
```

---

## 🔐 Security Considerations

1. **Access Control:**
   - Results only returned for tasks user created
   - Authentication required for all endpoints
   - JWT token validation

2. **Data Isolation:**
   - Results stored with task_id relationship
   - asset_id isolation for vulnerabilities
   - User-level access control

3. **Input Validation:**
   - Tool name validation against whitelist
   - Task existence verification
   - Target format validation

---

## 📱 Frontend Display Examples

### Overview Tab
Shows:
- Total tools executed
- Total findings count
- Vulnerability count
- Open ports count
- Severity distribution chart
- List of tools used

### Results Tab
Shows tool-specific formatting:

**FScan Results:**
- Table with IP, Port, Service, Version columns
- Sortable and filterable
- Pagination support

**Nuclei Results:**
- Table with Vulnerability, Severity, Matched URL
- Color-coded severity tags
- Pagination

**Afrog Results:**
- Table with Vulnerability, Severity, Target
- Expandable details

**DirSearch Results:**
- Table with Path, HTTP Status
- Status code color coding

### Raw Data Tab
Shows:
- Full JSON output
- Download button for each result
- Syntax highlighting

---

## 💾 Database Storage Schema

### TaskResult Table
```sql
CREATE TABLE task_results (
  id INTEGER PRIMARY KEY,
  task_id INTEGER NOT NULL FOREIGN KEY,
  result_type VARCHAR (e.g., "tool_fscan"),
  result_data JSON,
  created_at DATETIME
);
```

### Vulnerability Table (Enhanced)
```sql
CREATE TABLE vulnerabilities (
  id INTEGER PRIMARY KEY,
  asset_id INTEGER NOT NULL,
  poc_id INTEGER,
  title VARCHAR,
  description TEXT,
  cve_id VARCHAR,
  cvss_score FLOAT,
  severity VARCHAR,
  status VARCHAR,
  verified_at DATETIME,
  remediation TEXT,
  remediation_link VARCHAR,
  discovered_at DATETIME,
  created_at DATETIME,
  updated_at DATETIME
);
```

---

## 🔄 Workflow Example

### Complete End-to-End Flow

```
1. User creates task
   POST /api/v1/tasks
   Response: task_id = 5

2. Execute and store FScan results
   POST /api/v1/tools/task/5/execute-and-store
   - Executes FScan on target
   - Stores raw results in task_results
   - Extracts ports and creates vulnerability records
   - Returns statistics

3. View all results
   GET /api/v1/tools/task/5/results
   - Returns all tool results for task 5
   - Returns aggregated statistics
   - Shows tool-specific data

4. Generate report
   GET /api/v1/reports/task/5?format=html
   - Report includes tool findings
   - Shows vulnerabilities discovered by tools
   - Displays statistics

5. Frontend displays results
   <ToolResultsViewer taskId={5} />
   - Loads results from API
   - Displays in tabs (Overview, Results, Raw)
   - Allows download of raw JSON
```

---

## 🛠️ Configuration & Customization

### Modify Result Processing

To customize how results are processed, edit `ToolResultService`:

```python
@staticmethod
async def _process_fscan_results(...) -> int:
    # Add custom processing logic here
    # Modify title, severity, description
    # Add remediation suggestions
    # Create custom relationships
    pass
```

### Add New Tool

To add a new tool:

1. Add processing method to `ToolResultService`
2. Update `process_and_store_result` dispatcher
3. Update frontend `ToolResultsViewer` rendering

### Customize Frontend Display

Edit `ToolResultsViewer.tsx`:

```typescript
const renderCustomToolResults = (result: ToolResult) => {
  // Add custom rendering logic
  return <CustomTable data={result.data} />;
};
```

---

## 📊 Example Queries

### Get All Tool Results for a Task
```bash
curl "http://localhost:8000/api/v1/tools/task/5/results" \
  -H "Authorization: Bearer $TOKEN"
```

### Get Only Nuclei Results
```bash
curl "http://localhost:8000/api/v1/tools/task/5/results?tool_name=nuclei" \
  -H "Authorization: Bearer $TOKEN"
```

### Execute FScan and Store
```bash
curl -X POST "http://localhost:8000/api/v1/tools/task/5/execute-and-store" \
  -H "Authorization: Bearer $TOKEN" \
  -d "tool_name=fscan&target=192.168.1.0/24&options={\"threads\":50}"
```

### Get Statistics
```bash
# Included in results response
curl "http://localhost:8000/api/v1/tools/task/5/results" \
  -H "Authorization: Bearer $TOKEN" | jq '.data.statistics'
```

---

## 🚨 Error Handling

### Common Errors

**Error: Tool not installed**
```json
{
  "detail": "Tool 'afrog' is not installed"
}
```
**Solution:** Install the tool first

**Error: Task not found**
```json
{
  "detail": "Task 5 not found"
}
```
**Solution:** Verify task_id exists

**Error: Tool execution failed**
```json
{
  "detail": "Tool execution and storage failed: timeout"
}
```
**Solution:** Increase timeout, check target availability

---

## 📈 Performance Optimization

### Indexing
The database uses indexes on:
- `task_id` (TaskResult)
- `asset_id` (Vulnerability)
- `severity` (Vulnerability)
- `discovered_at` (Vulnerability)

### Pagination
Results are paginated in frontend for large datasets:
- FScan: 10 ports per page
- Nuclei: 10 vulnerabilities per page
- DirSearch: 10 directories per page

### Caching
Consider implementing caching for:
- Task statistics (TTL: 5 minutes)
- Tool result list (TTL: 2 minutes)
- Vulnerability counts (TTL: 10 minutes)

---

## 🔍 Monitoring & Logging

All operations are logged:

```python
# Successful storage
logger.info(f"Tool result stored for task {task_id}: {tool_name}, findings: {findings_count}")

# Errors
logger.error(f"Error processing tool result: {e}")
logger.warning(f"Error processing {tool_name} results: {e}")
```

Monitor logs for:
- Tool execution failures
- Database storage errors
- API processing failures

---

## 📚 API Reference Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/tools/task/{id}/results` | GET | Get stored tool results |
| `/api/v1/tools/task/{id}/execute-and-store` | POST | Execute and store results |
| `/api/v1/tools/execute` | POST | Execute tool only (no storage) |
| `/api/v1/tools/chain/execute` | POST | Execute multiple tools |

---

## ✅ Checklist for Implementation

- [x] Backend service created (ToolResultService)
- [x] API endpoints implemented
- [x] Database storage working
- [x] Tool-specific result processing
- [x] Frontend component created (ToolResultsViewer)
- [x] Statistics aggregation
- [x] Error handling
- [x] Documentation complete

---

## 🎯 Next Steps

1. **Test Integration:**
   - Execute each tool and verify storage
   - Check frontend display
   - Validate data extraction

2. **Performance Testing:**
   - Load test with large results
   - Monitor database performance
   - Optimize queries if needed

3. **Feature Enhancement:**
   - Add export to CSV/JSON
   - Implement filtering and sorting
   - Add comparison between scans
   - Create trend analysis

---

**Status:** ✅ Ready to use

**Last Updated:** November 12, 2025

**Support:** See TOOL_INTEGRATION_GUIDE.md for general tool usage
