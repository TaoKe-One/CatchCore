# Tool Integration Guide - CatchCore

**Version:** 1.0
**Date:** 2025-11-12
**Status:** Production Ready

---

## 📋 Overview

CatchCore integrates 5 industry-leading security scanning tools into a unified API interface:

| Tool | Purpose | Status |
|------|---------|--------|
| **Afrog** | Vulnerability scanning & PoC execution | ✅ Integrated |
| **DDDD** | Advanced vulnerability scanning | ✅ Integrated |
| **FScan** | Port scanning & service detection | ✅ Integrated |
| **Nuclei** | Template-based vulnerability scanning | ✅ Integrated |
| **DirSearch** | Directory enumeration & discovery | ✅ Integrated |

---

## 🚀 Quick Start

### 1. Installation

Install required tools on your system:

```bash
# Afrog - Security scanning framework
go install -v github.com/zan8in/afrog@latest

# DDDD - Advanced vulnerability scanner
git clone https://github.com/SleepingBag945/dddd.git
cd dddd && chmod +x dddd

# FScan - High-performance network scanner
git clone https://github.com/shadow1ng/fscan.git
cd fscan && chmod +x fscan

# Nuclei - Template-based vulnerability scanner
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

# DirSearch - Directory enumeration tool
git clone https://github.com/maurosoria/dirsearch.git
cd dirsearch && chmod +x dirsearch.py
```

### 2. Check Available Tools

```bash
curl http://localhost:8000/api/v1/tools/available \
  -H "Authorization: Bearer $TOKEN"
```

Response:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "tools": { ... },
    "installed": {
      "afrog": true,
      "dddd": true,
      "fscan": true,
      "nuclei": true,
      "dirsearch": true
    },
    "summary": {
      "total": 5,
      "installed_count": 5,
      "available_count": 0
    }
  }
}
```

### 3. Execute a Tool

```bash
# Port scan with FScan
curl "http://localhost:8000/api/v1/tools/execute?tool_name=fscan&target=192.168.1.100" \
  -H "Authorization: Bearer $TOKEN"

# Vulnerability scan with Nuclei
curl "http://localhost:8000/api/v1/tools/execute?tool_name=nuclei&target=http://example.com" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📚 API Reference

### Tool Management Endpoints

#### 1. Get Available Tools

```
GET /api/v1/tools/available
```

Returns list of available tools and their installation status.

**Response:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "tools": {
      "afrog": {
        "name": "Afrog",
        "description": "Framework for security scanning and PoC verification",
        "url": "https://github.com/zan8in/afrog",
        "capabilities": ["vulnerability_scanning", "poc_execution"],
        "output_format": "json"
      },
      ...
    },
    "installed": { ... },
    "summary": { ... }
  }
}
```

#### 2. Get Tool Status

```
GET /api/v1/tools/status
```

Returns detailed status for all tools including installation status and capabilities.

**Response:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "afrog": {
      "name": "Afrog",
      "description": "...",
      "installed": true,
      "capabilities": [...],
      "output_format": "json"
    },
    ...
  }
}
```

#### 3. Get Tool Information

```
GET /api/v1/tools/{tool_name}/info
```

Get detailed information about a specific tool.

**Parameters:**
- `tool_name` (path): Tool name (afrog, dddd, fscan, nuclei, dirsearch)

**Response:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "name": "FScan",
    "description": "High-performance network scanner",
    "url": "https://github.com/shadow1ng/fscan",
    "installed": true,
    "capabilities": ["port_scanning", "service_detection"],
    "output_format": "json",
    "usage_examples": {
      "single_host": "/api/v1/tools/execute?tool_name=fscan&target=192.168.1.100",
      "cidr_range": "/api/v1/tools/execute?tool_name=fscan&target=192.168.1.0/24",
      "specific_ports": "/api/v1/tools/execute?tool_name=fscan&target=192.168.1.100&ports=22,80,443"
    }
  }
}
```

---

### Tool Execution Endpoints

#### 1. Execute Single Tool

```
POST /api/v1/tools/execute
```

Execute a single security tool on a target.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tool_name` | string | ✅ | Tool to execute (afrog, dddd, fscan, nuclei, dirsearch) |
| `target` | string | ✅ | Target IP, URL, or CIDR range |
| `poc_file` | string | ❌ | POC file path (for afrog) |
| `templates` | string | ❌ | Template filter (for nuclei) |
| `timeout` | integer | ❌ | Command timeout in seconds (default: 300-600) |
| `threads` | integer | ❌ | Number of worker threads (1-100) |
| `ports` | string | ❌ | Port specification, e.g., "22,80,443" (for fscan) |
| `wordlist` | string | ❌ | Wordlist path (for dirsearch) |
| `extensions` | string | ❌ | File extensions, e.g., "php,html,txt" (for dirsearch) |

**Examples:**

**FScan Port Scan:**
```bash
curl "http://localhost:8000/api/v1/tools/execute?tool_name=fscan&target=192.168.1.100&timeout=300" \
  -H "Authorization: Bearer $TOKEN"
```

**Nuclei Vulnerability Scan:**
```bash
curl "http://localhost:8000/api/v1/tools/execute?tool_name=nuclei&target=http://example.com&templates=cves&timeout=600" \
  -H "Authorization: Bearer $TOKEN"
```

**Afrog with POC:**
```bash
curl "http://localhost:8000/api/v1/tools/execute?tool_name=afrog&target=http://example.com&poc_file=/path/to/poc.yaml&threads=10" \
  -H "Authorization: Bearer $TOKEN"
```

**DirSearch with Custom Wordlist:**
```bash
curl "http://localhost:8000/api/v1/tools/execute?tool_name=dirsearch&target=http://example.com&wordlist=/path/to/wordlist.txt&extensions=php,html" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "tool": "fscan",
    "target": "192.168.1.100",
    "status": "success",
    "ports_found": 8,
    "results": [
      {
        "ip": "192.168.1.100",
        "port": 22,
        "service": "ssh",
        "version": "OpenSSH 7.4"
      },
      ...
    ],
    "raw_output": "..."
  }
}
```

#### 2. Execute Tool Chain

```
POST /api/v1/tools/chain/execute
```

Execute multiple tools sequentially on a target and aggregate results.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `target` | string | ✅ | Target IP, URL, or CIDR range |
| `tools` | string | ✅ | Comma-separated tool names (e.g., "fscan,nuclei,afrog") |
| `timeout` | integer | ❌ | Command timeout in seconds |
| `threads` | integer | ❌ | Number of worker threads (1-100) |

**Example:**

```bash
curl "http://localhost:8000/api/v1/tools/chain/execute?target=192.168.1.100&tools=fscan,nuclei,afrog&timeout=600" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "target": "192.168.1.100",
    "timestamp": "2025-11-12T10:30:45.123456",
    "tools_executed": ["fscan", "nuclei", "afrog"],
    "total_vulnerabilities": 12,
    "total_services": 8,
    "total_directories": 45,
    "tool_results": {
      "fscan": {
        "tool": "fscan",
        "status": "success",
        "ports_found": 8,
        "results": [...]
      },
      "nuclei": {
        "tool": "nuclei",
        "status": "success",
        "vulnerabilities_found": 4,
        "results": [...]
      },
      "afrog": {
        "tool": "afrog",
        "status": "success",
        "vulnerabilities_found": 8,
        "results": [...]
      }
    }
  }
}
```

#### 3. Execute Tool with Task Integration

```
POST /api/v1/tools/execute-with-task
```

Execute a tool and store results in the task management system for tracking and reporting.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | integer | ✅ | Task ID to associate with execution |
| `tool_name` | string | ✅ | Tool name |
| `target` | string | ✅ | Target address |
| `options` | object | ❌ | Tool-specific options |

**Example:**

```bash
curl "http://localhost:8000/api/v1/tools/execute-with-task?task_id=5&tool_name=fscan&target=192.168.1.100" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": 5,
    "tool": "fscan",
    "result": { ... },
    "stored": true
  }
}
```

---

## 🔧 Tool-Specific Configuration

### AFrog

**Description:** Framework for security scanning and PoC verification

**Capabilities:**
- Vulnerability scanning
- PoC execution

**Required Parameters:**
- `target`: URL or IP address

**Optional Parameters:**
- `poc_file`: Path to POC file (YAML format)
- `timeout`: Scan timeout in seconds (default: 300)
- `threads`: Number of threads (default: 10)

**Example:**
```bash
curl "http://localhost:8000/api/v1/tools/execute?tool_name=afrog&target=http://example.com&threads=20&timeout=600" \
  -H "Authorization: Bearer $TOKEN"
```

**Output Format:** JSON

---

### DDDD

**Description:** Advanced vulnerability scanning tool

**Capabilities:**
- Vulnerability scanning
- Host discovery

**Required Parameters:**
- `target`: IP address or domain

**Optional Parameters:**
- `timeout`: Scan timeout in seconds
- `threads`: Number of worker threads

**Example:**
```bash
curl "http://localhost:8000/api/v1/tools/execute?tool_name=dddd&target=192.168.1.100&timeout=300" \
  -H "Authorization: Bearer $TOKEN"
```

**Output Format:** JSON

---

### FScan

**Description:** High-performance network scanner

**Capabilities:**
- Port scanning
- Service detection

**Required Parameters:**
- `target`: Single IP or CIDR range (e.g., 192.168.1.0/24)

**Optional Parameters:**
- `ports`: Specific ports to scan (e.g., "22,80,443,3306")
- `timeout`: Scan timeout in seconds
- `threads`: Number of worker threads (1-100)

**Examples:**

Single Host:
```bash
curl "http://localhost:8000/api/v1/tools/execute?tool_name=fscan&target=192.168.1.100" \
  -H "Authorization: Bearer $TOKEN"
```

CIDR Range:
```bash
curl "http://localhost:8000/api/v1/tools/execute?tool_name=fscan&target=192.168.1.0/24&threads=50" \
  -H "Authorization: Bearer $TOKEN"
```

Specific Ports:
```bash
curl "http://localhost:8000/api/v1/tools/execute?tool_name=fscan&target=192.168.1.100&ports=22,80,443,3306,5432" \
  -H "Authorization: Bearer $TOKEN"
```

**Output Format:** JSON (one object per line)

---

### Nuclei

**Description:** Fast and customizable vulnerability scanner

**Capabilities:**
- Vulnerability scanning
- PoC execution
- Web scanning

**Required Parameters:**
- `target`: URL or IP address

**Optional Parameters:**
- `templates`: Template filter (e.g., "cves", "osint", "web")
- `timeout`: Scan timeout in seconds
- `severity`: Filter by severity (critical, high, medium, low, info)
- `threads`: Concurrency level (1-100)

**Examples:**

CVE Scanning:
```bash
curl "http://localhost:8000/api/v1/tools/execute?tool_name=nuclei&target=http://example.com&templates=cves&severity=critical" \
  -H "Authorization: Bearer $TOKEN"
```

OSINT:
```bash
curl "http://localhost:8000/api/v1/tools/execute?tool_name=nuclei&target=example.com&templates=osint" \
  -H "Authorization: Bearer $TOKEN"
```

**Output Format:** JSON (one object per line)

---

### DirSearch

**Description:** Directory enumeration and discovery tool

**Capabilities:**
- Directory enumeration
- Web enumeration

**Required Parameters:**
- `target`: Target URL (must start with http:// or https://)

**Optional Parameters:**
- `wordlist`: Custom wordlist file path
- `extensions`: File extensions to search for (e.g., "php,html,txt,jsp")
- `timeout`: Scan timeout in seconds
- `threads`: Number of worker threads

**Examples:**

Basic Enumeration:
```bash
curl "http://localhost:8000/api/v1/tools/execute?tool_name=dirsearch&target=http://example.com" \
  -H "Authorization: Bearer $TOKEN"
```

Custom Wordlist:
```bash
curl "http://localhost:8000/api/v1/tools/execute?tool_name=dirsearch&target=http://example.com&wordlist=/path/to/wordlist.txt&extensions=php,html,asp" \
  -H "Authorization: Bearer $TOKEN"
```

**Output Format:** Text (parseable)

---

## 🔄 Integration Workflow

### Workflow 1: Single Tool Execution

```
User Request
    ↓
[API: /tools/execute]
    ↓
[Validation]
  - Tool exists?
  - Tool installed?
    ↓
[Execute Tool]
  - Build command
  - Run subprocess
  - Parse output
    ↓
[Return Results]
  - Format response
  - Include metadata
```

### Workflow 2: Tool Chain Execution

```
User Request with Tool List
    ↓
[API: /tools/chain/execute]
    ↓
[Validation]
  - All tools exist?
  - All tools installed?
    ↓
[Execute Sequential]
  Tool 1 → Parse Results
    ↓
  Tool 2 → Parse Results
    ↓
  Tool 3 → Parse Results
    ↓
[Aggregate Results]
  - Combine findings
  - Count vulnerabilities
  - Count services
  - Count directories
    ↓
[Return Combined Results]
```

### Workflow 3: Task-Integrated Execution

```
User Request
    ↓
[API: /tools/execute-with-task]
    ↓
[Verify Task]
  - Task exists?
  - User authorized?
    ↓
[Execute Tool]
    ↓
[Store Results]
  - Save to TaskResult table
  - Update task status
    ↓
[Return Response]
  - Include task_id
  - Include stored flag
```

---

## 📊 Result Structures

### FScan Result

```json
{
  "tool": "fscan",
  "target": "192.168.1.100",
  "status": "success",
  "ports_found": 8,
  "results": [
    {
      "ip": "192.168.1.100",
      "port": 22,
      "service": "SSH",
      "version": "OpenSSH_7.4"
    },
    {
      "ip": "192.168.1.100",
      "port": 80,
      "service": "HTTP",
      "version": "Apache/2.4.6"
    }
  ],
  "raw_output": "..."
}
```

### Nuclei Result

```json
{
  "tool": "nuclei",
  "target": "http://example.com",
  "status": "success",
  "vulnerabilities_found": 5,
  "results": [
    {
      "id": "cve-2021-41773",
      "name": "Apache 2.4.49/2.4.50 - Remote Code Execution",
      "severity": "critical",
      "description": "...",
      "matched_at": "http://example.com/cgi-bin/"
    }
  ],
  "raw_output": "..."
}
```

### Afrog Result

```json
{
  "tool": "afrog",
  "target": "http://example.com",
  "status": "success",
  "vulnerabilities_found": 3,
  "results": [
    {
      "vulnerability": "SQL Injection",
      "severity": "high",
      "target": "http://example.com/login",
      "description": "..."
    }
  ],
  "raw_output": "..."
}
```

---

## 🛠️ Error Handling

### Common Errors

**Tool Not Found:**
```json
{
  "detail": "Unknown tool: xyz. Supported tools: afrog, dddd, fscan, nuclei, dirsearch"
}
```

**Tool Not Installed:**
```json
{
  "detail": "Tool 'afrog' is not installed. Please install from: https://github.com/zan8in/afrog"
}
```

**Execution Timeout:**
```json
{
  "detail": "Tool execution failed: Scan timeout"
}
```

**Invalid Target:**
```json
{
  "detail": "Tool execution failed: Invalid target format"
}
```

---

## 🔐 Security Considerations

1. **Input Validation:**
   - All tool names are validated against whitelist
   - Target addresses are validated for format
   - File paths are checked for existence (when required)

2. **Timeout Protection:**
   - All tools have maximum timeout (300-600 seconds)
   - Processes are forcefully terminated on timeout
   - Prevents resource exhaustion

3. **Output Sanitization:**
   - Raw output limited to 1000 characters
   - JSON output properly parsed and validated
   - Error messages don't expose system paths

4. **Authorization:**
   - All endpoints require authentication
   - User context is maintained
   - Results can be associated with tasks for audit trail

---

## 📈 Performance Tuning

### Thread Optimization

For FScan CIDR scanning:
```bash
# Small network (< 256 hosts)
threads=10

# Medium network (256-1000 hosts)
threads=20-30

# Large network (> 1000 hosts)
threads=50-100
```

### Timeout Configuration

- **FScan:** 300-600 seconds (based on network size)
- **Nuclei:** 300-900 seconds (depends on templates)
- **Afrog:** 300-600 seconds
- **DirSearch:** 300-900 seconds
- **DDDD:** 300-600 seconds

### Parallel Execution

For tool chains, consider tool dependencies:

**Recommended order:**
1. FScan (port discovery) - ~5 minutes
2. Nuclei (vulnerability scanning) - ~10 minutes
3. Afrog (PoC validation) - ~5 minutes
4. DirSearch (directory enumeration) - ~10 minutes

---

## 🔗 Integration Examples

### Example 1: Complete Network Assessment

```bash
#!/bin/bash

TOKEN="your_jwt_token"
TARGET="192.168.1.0/24"

# Step 1: Port scanning
echo "Step 1: Scanning ports..."
curl -s "http://localhost:8000/api/v1/tools/execute?tool_name=fscan&target=$TARGET&threads=50" \
  -H "Authorization: Bearer $TOKEN" | jq '.data.results' > ports.json

# Step 2: Vulnerability scanning
echo "Step 2: Scanning vulnerabilities..."
curl -s "http://localhost:8000/api/v1/tools/execute?tool_name=nuclei&target=$TARGET&templates=cves" \
  -H "Authorization: Bearer $TOKEN" | jq '.data.results' > vulns.json

# Step 3: Generate report
echo "Step 3: Generating report..."
FINDINGS=$(jq -r 'length' ports.json)
echo "Found $FINDINGS services and vulnerabilities"
```

### Example 2: Task-Integrated Scanning

```bash
#!/bin/bash

TOKEN="your_jwt_token"
TASK_ID=5
TARGET="http://example.com"

# Execute FScan and store in task
curl -s "http://localhost:8000/api/v1/tools/execute-with-task?task_id=$TASK_ID&tool_name=fscan&target=$TARGET" \
  -H "Authorization: Bearer $TOKEN"

# Execute Nuclei and store in task
curl -s "http://localhost:8000/api/v1/tools/execute-with-task?task_id=$TASK_ID&tool_name=nuclei&target=$TARGET" \
  -H "Authorization: Bearer $TOKEN"

# View task results via /api/v1/reports/task/{task_id}
curl -s "http://localhost:8000/api/v1/reports/task/$TASK_ID?format=html" \
  -H "Authorization: Bearer $TOKEN" > report.html
```

---

## 📝 Logging and Monitoring

### Log Files

All tool executions are logged to:
- Standard application logs: `logs/app.log`
- Tool-specific logs: `logs/tools.log`

### Example Log Entry

```
2025-11-12 10:30:45,123 - tool_integration - INFO - Starting FScan scan on 192.168.1.100
2025-11-12 10:30:45,456 - tool_integration - DEBUG - Executing: fscan -h 192.168.1.100 -p 22,80,443 -json
2025-11-12 10:32:15,789 - tool_integration - INFO - Tool execution completed: fscan on 192.168.1.100, status: success
```

---

## 🚀 Deployment Checklist

- [ ] All required tools installed on server
- [ ] Tool binaries in system PATH or configured paths
- [ ] File permissions set correctly for tool execution
- [ ] Timeout values configured appropriately
- [ ] API authentication enabled
- [ ] Rate limiting configured (if needed)
- [ ] Logging configured and rotated
- [ ] Database tables created for TaskResult
- [ ] API documentation accessible at /docs
- [ ] Health check passing: `GET /health`

---

## 📞 Troubleshooting

### Tool Not Found Error

**Problem:** "Tool 'afrog' is not installed"

**Solution:**
```bash
# Verify tool is installed
which afrog

# Add to PATH if necessary
export PATH=$PATH:/usr/local/go/bin
export PATH=$PATH:$HOME/go/bin

# Test tool directly
afrog --version
```

### Command Timeout

**Problem:** "Scan timeout"

**Solution:**
```bash
# Increase timeout parameter
curl "http://localhost:8000/api/v1/tools/execute?tool_name=fscan&target=192.168.1.0/24&timeout=900" \
  -H "Authorization: Bearer $TOKEN"
```

### Invalid JSON Output

**Problem:** "Failed to parse tool JSON output"

**Solution:**
- Check if tool is producing valid JSON
- Test tool manually: `nuclei -target example.com -json | jq .`
- Check tool version compatibility

---

## 📚 Additional Resources

- **Afrog Docs:** https://github.com/zan8in/afrog
- **DDDD Docs:** https://github.com/SleepingBag945/dddd
- **FScan Docs:** https://github.com/shadow1ng/fscan
- **Nuclei Docs:** https://nuclei.projectdiscovery.io/
- **DirSearch Docs:** https://github.com/maurosoria/dirsearch

---

## 🎯 Next Steps

1. **Install all tools** on your system
2. **Verify installation** using `/api/v1/tools/available`
3. **Test individual tools** with `/api/v1/tools/execute`
4. **Create scanning workflows** using `/api/v1/tools/chain/execute`
5. **Integrate with tasks** using `/api/v1/tools/execute-with-task`
6. **Generate reports** from results using `/api/v1/reports`

---

**Last Updated:** 2025-11-12
**Maintainer:** CatchCore Development Team
