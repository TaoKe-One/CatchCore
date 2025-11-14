# CatchCore：漏洞猎手的"核心捕鼠器"

**——让内网安全风险无处可逃**

## 🔍 项目起源：从"猫抓老鼠"到"漏洞猎人"

在网络安全的世界里，漏洞就像潜伏在暗处的"老鼠"，它们可能藏在代码的缝隙、配置的漏洞或未更新的系统中，随时可能被攻击者利用，造成数据泄露、业务中断甚至灾难性后果。而传统的安全防护工具，往往像"笨拙的猫"，只能被动等待老鼠出现，却无法主动发现并消灭它们。

**CatchCore的诞生**，正是为了打造一只"顶尖的捕鼠猫"——它不仅能主动嗅探内网中的每一个漏洞，还能精准定位风险、量化威胁，并为企业提供可执行的修复建议。正如"抓到老鼠的猫才是好猫"，CatchCore的核心目标只有一个：**让漏洞无处藏身，让安全风险可控**。

---

## 1. 项目概述

### 项目描述
CatchCore 是一款综合性内网安全检测和运维工具，专门针对企业内部网络进行快速资产发现、识别、检测和漏洞评估。通过集成多个开源安全工具，实现自动化漏洞探测、修复验证和资产管理的完整闭环。让安全团队从被动防守转变为主动出击，以"捕鼠器"般的精准高效，捉住每一只潜在的"漏洞老鼠"。

### 主要目标
1. **资产发现与识别**：快速发现内网资产，建立完整的资产信息库
2. **薄弱点识别**：识别系统和服务中存在的安全漏洞和攻击面
3. **自动化检测**：通过集成工具实现多维度的自动化扫描和POC验证
4. **修复验证**：支持漏洞修复后的复测功能，验证修复有效性
5. **分布式部署**：支持多节点部署，适应大规模内网环境

### 核心价值
- 提高企业安全团队的工作效率
- 建立完整的内网资产和漏洞管理体系
- 支持安全运维的持续改进
- 降低内网安全风险

---

## 2. 技术栈

### 前端
- **框架**：React 18 + TypeScript
- **UI库**：Ant Design v5、Echarts（数据可视化）
- **状态管理**：Redux Toolkit / Zustand
- **HTTP客户端**：axios
- **构建工具**：Vite
- **样式**：Tailwind CSS + LESS

### 后端
- **语言**：Python 3.10+、Go（高性能扫描引擎）
- **框架**：FastAPI（Python）/ Gin（Go）
- **任务队列**：Celery + Redis
- **实时通信**：WebSocket（扫描进度推送）
- **认证**：JWT + OAuth2

### 数据库
- **主数据库**：PostgreSQL 14+（关系数据存储）
- **缓存层**：Redis 7+（会话、缓存、消息队列）
- **时序数据**：InfluxDB（扫描历史、趋势分析）
- **搜索引擎**：Elasticsearch（资产数据全文搜索）

### 第三方工具集成
- **afrog**：综合漏洞扫描器
- **dddd**：DNS和子域名扫描
- **fscan**：内网扫描工具
- **nuclei**：POC框架和漏洞验证
- **dirsearch**：目录扫描工具
- **hydra/medusa**：弱口令破解
- **nmap**：端口扫描和服务识别

### 部署
- **容器化**：Docker + Docker Compose
- **编排**：Kubernetes（可选）
- **监控**：Prometheus + Grafana
- **日志**：ELK Stack

---

## 3. 功能需求

### 3.1 用户管理
- **用户注册**：新用户自注册或管理员创建
- **用户登录**：支持用户名密码、LDAP集成
- **用户信息管理**：编辑用户资料、修改密码、头像上传
- **权限管理**：基于角色的访问控制（RBAC）
  - 管理员：全部权限
  - 安全主管：查看、导出报告，修改POC库
  - 安全运维：执行扫描、管理任务
  - 审计员：只读权限
- **多租户支持**：为不同部门创建独立的工作空间

### 3.2 资产管理
- **资产导入**：支持IP段、IP列表、域名批量导入
- **资产分组**：按业务、部门、环境等维度分组
- **资产详情页**：展示资产的所有扫描结果、漏洞、服务信息
- **资产标签**：动态标签管理，快速筛选资产
- **资产导出**：支持CSV、Excel导出

### 3.3 端口探测与服务识别
- **端口扫描**：
  - 集成nmap和fscan进行快速端口扫描
  - 支持自定义扫描范围、速率限制
  - 扫描结果实时显示
  
- **服务识别**：
  - 自动识别开放端口上的服务类型
  - 识别服务版本信息
  - 关联已知漏洞

- **Web识别**：
  - 识别HTTP/HTTPS服务
  - 自动爬取robots.txt、sitemap.xml
  - 收集Web服务指纹

### 3.4 指纹识别与系统识别
- **内置指纹库**：52000+条指纹数据
- **性能指标**：1万个Web系统指纹识别耗时8-10分钟
- **识别维度**：
  - 操作系统指纹
  - Web框架和CMS识别
  - 中间件识别（Tomcat、IIS、Nginx等）
  - 应用软件识别
- **动态指纹更新**：支持上传自定义指纹规则

### 3.5 POC验证与漏洞检测
- **POC库管理**：
  - 内置POC库（基于afrog和nuclei）
  - 支持上传自定义POC
  - POC版本管理和更新
  - POC按CVE、产品、类型分类

- **POC执行**：
  - 单个或批量执行POC验证
  - 按发现的服务自动匹配和触发POC
  - 支持POC参数自定义
  - 实时显示验证进度和结果

- **漏洞报告**：
  - 漏洞详情展示（CVSS评分、影响范围、修复方案）
  - 漏洞分类和标签
  - 漏洞去重和聚合

### 3.6 弱口令猜解
- **密码破解**：
  - 集成hydra/medusa工具
  - 支持SSH、FTP、Telnet、HTTP等多种协议
  - 可配置字典库和扫描速率
  - 扫描结果记录和管理

- **字典管理**：
  - 内置常用字典（默认口令等）
  - 支持自定义字典上传
  - 字典版本管理

### 3.7 目录扫描
- **集成dirsearch**：
  - 批量扫描Web目录
  - 支持自定义扫描路径
  - 发现隐藏目录、备份文件、配置文件
  - 结果去重和聚合

- **URL Finder**：
  - 自动采集和解析URL
  - 支持参数提取和分类
  - URL去重和统计

### 3.8 扫描任务管理
- **任务创建**：
  - 支持创建IP端口扫描任务
  - URL扫描任务
  - POC检测任务
  - 密码破解任务
  - 目录扫描任务

- **任务关联**：在创建扫描任务时，可关联多个检测模块：
  - IP端口扫描 → 自动触发服务识别、POC检测
  - 服务识别 → 自动匹配并执行密码破解
  - Web识别 → 自动执行目录扫描、URL扫描

- **任务调度**：
  - 支持即时执行、定时执行、周期执行
  - 任务优先级设置
  - 任务队列管理（支持暂停、继续、取消）

- **任务日志**：详细的执行日志记录

### 3.9 漏洞管理
- **漏洞列表**：汇总所有发现的漏洞
  - 按严重程度分类（Critical、High、Medium、Low）
  - 按状态分类（新发现、已处理、已关闭、误报）
  - 按资产、POC、类型多维度筛选

- **漏洞详情**：
  - 漏洞名称、CVE ID、CVSS评分
  - 影响资产列表
  - 修复建议和参考链接
  - 关联的POC和扫描记录

- **漏洞修复与复测**：
  - 标记漏洞状态为"已修复"
  - 执行复测扫描
  - 对比修复前后的扫描结果
  - 生成修复报告

- **漏洞统计**：
  - 漏洞数量趋势图
  - 按严重程度的分布
  - 按资产的分布
  - 修复率统计

### 3.10 项目管理
- **项目创建**：为不同的安全评估项目创建独立空间
- **项目配置**：
  - 项目基本信息（名称、描述、时间范围）
  - 扫描范围配置
  - 检测模块启用/禁用
  - 通知设置

- **项目报告**：
  - 生成项目汇总报告
  - 导出PDF/Excel格式
  - 报告模板自定义

### 3.11 节点管理（分布式部署）
- **节点注册**：新节点自注册到中心控制台
- **节点状态**：实时显示各节点的在线状态、资源使用情况
- **任务分发**：根据节点能力和负载自动分发扫描任务
- **节点监控**：CPU、内存、磁盘、网络等性能指标

### 3.12 数据管理与报告
- **数据导出**：
  - 导出扫描结果（CSV、Excel、JSON）
  - 导出漏洞清单
  - 导出资产清单

- **报告生成**：
  - 自动生成安全评估报告
  - 支持报告模板编辑
  - 生成时间线式的漏洞发现报告
  - 支持报告签名和加密

---

## 4. 非功能需求

### 性能要求
- **响应时间**：API平均响应时间 < 500ms
- **并发能力**：支持至少100个并发扫描任务
- **指纹识别效率**：1万个Web系统指纹识别 < 10分钟
- **数据库查询**：资产列表查询 < 1秒

### 安全要求
- **身份认证**：使用JWT + OAuth2，支持多因素认证（MFA）
- **数据加密**：
  - 传输层：TLS 1.3
  - 存储层：敏感数据加密存储（如口令字典）
  - 数据库连接加密

- **访问控制**：严格的RBAC权限管理
- **审计日志**：所有敏感操作的详细日志记录
- **安全加固**：
  - SQL注入防护
  - XSS防护
  - CSRF防护
  - 速率限制

### 可扩展性
- **模块化设计**：各功能模块独立，便于扩展
- **工具集成接口**：标准化的工具集成API，便于接入新的扫描工具
- **POC框架**：支持多种POC格式（Nuclei、自定义脚本等）
- **插件系统**：支持第三方插件开发

### 并发处理
- **消息队列**：使用Redis + Celery处理异步任务
- **分布式锁**：防止任务重复执行
- **负载均衡**：多个扫描节点的负载均衡
- **资源限流**：防止单个任务占用过多资源

---

## 5. 数据库设计

### 主要表结构

#### 用户和权限
- `users`：用户表（id, username, email, password_hash, status, created_at）
- `roles`：角色表（id, name, description）
- `permissions`：权限表（id, name, description）
- `user_roles`：用户角色关系表（user_id, role_id）
- `role_permissions`：角色权限关系表（role_id, permission_id）

#### 资产管理
- `assets`：资产表（id, ip, hostname, os, status, tags, department, environment, created_at, updated_at）
- `asset_groups`：资产分组表（id, name, description, project_id）
- `asset_group_members`：资产分组成员表（group_id, asset_id）
- `services`：服务表（id, asset_id, port, protocol, service_name, version, fingerprint, discovered_at）

#### 指纹库
- `fingerprints`：指纹表（id, name, type, pattern, regex, product, vendor, category, created_at）
- `fingerprint_matches`：指纹匹配记录表（id, asset_id, fingerprint_id, matched_info, matched_at）

#### POC和漏洞
- `pocs`：POC表（id, name, cve_id, cvss_score, severity, type, content, source, updated_at）
- `poc_tags`：POC标签表（poc_id, tag）
- `vulnerabilities`：漏洞表（id, asset_id, poc_id, status, verified_at, remediation, created_at）
- `vulnerability_history`：漏洞历史表（id, vulnerability_id, status, notes, operator, timestamp）

#### 扫描任务
- `tasks`：任务表（id, task_type, name, target_range, status, created_by, created_at, started_at, finished_at）
- `task_configs`：任务配置表（id, task_id, config_key, config_value）
- `task_results`：任务结果表（id, task_id, result_type, result_data, created_at）
- `task_logs`：任务日志表（id, task_id, log_level, log_message, timestamp）

#### 弱口令
- `credentials`：凭证表（id, asset_id, protocol, username, password_hash, status, created_at）
- `dictionaries`：字典表（id, name, type, path, count）

#### 项目管理
- `projects`：项目表（id, name, description, start_date, end_date, scope, status）
- `project_assets`：项目资产关系表（project_id, asset_id）
- `project_tasks`：项目任务关系表（project_id, task_id）

#### 节点管理
- `nodes`：节点表（id, name, host, port, status, cpu_usage, memory_usage, disk_usage, last_heartbeat）

### 表之间的关系

```
用户 → 任务（一对多）
用户 → 项目（多对多）
资产 → 服务（一对多）
资产 → 漏洞（一对多）
资产 → 指纹匹配（一对多）
资产 → 凭证（一对多）
POC → 漏洞（一对多）
任务 → 任务结果（一对多）
任务 → 任务日志（一对多）
项目 → 资产（多对多）
项目 → 任务（多对多）
```

---

## 6. API 设计

### 认证接口
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/logout` - 用户登出
- `POST /api/auth/refresh-token` - 刷新令牌

### 用户管理接口
- `GET /api/users` - 获取用户列表
- `GET /api/users/{id}` - 获取用户详情
- `POST /api/users` - 创建用户
- `PUT /api/users/{id}` - 更新用户信息
- `DELETE /api/users/{id}` - 删除用户

### 资产管理接口
- `GET /api/assets` - 获取资产列表（支持分页、筛选、排序）
- `GET /api/assets/{id}` - 获取资产详情
- `POST /api/assets` - 创建资产
- `POST /api/assets/batch-import` - 批量导入资产
- `PUT /api/assets/{id}` - 更新资产
- `DELETE /api/assets/{id}` - 删除资产
- `GET /api/assets/{id}/services` - 获取资产的服务列表
- `GET /api/assets/{id}/vulnerabilities` - 获取资产的漏洞列表

### 扫描任务接口
- `POST /api/tasks` - 创建扫描任务
- `GET /api/tasks` - 获取任务列表
- `GET /api/tasks/{id}` - 获取任务详情
- `PUT /api/tasks/{id}` - 更新任务
- `DELETE /api/tasks/{id}` - 删除任务
- `POST /api/tasks/{id}/start` - 启动任务
- `POST /api/tasks/{id}/pause` - 暂停任务
- `POST /api/tasks/{id}/resume` - 恢复任务
- `POST /api/tasks/{id}/cancel` - 取消任务
- `GET /api/tasks/{id}/progress` - 获取任务进度（WebSocket）
- `GET /api/tasks/{id}/logs` - 获取任务日志

### 漏洞管理接口
- `GET /api/vulnerabilities` - 获取漏洞列表
- `GET /api/vulnerabilities/{id}` - 获取漏洞详情
- `PUT /api/vulnerabilities/{id}` - 更新漏洞状态
- `POST /api/vulnerabilities/{id}/retest` - 复测漏洞
- `DELETE /api/vulnerabilities/{id}` - 删除漏洞
- `GET /api/vulnerabilities/stats` - 获取漏洞统计

### POC管理接口
- `GET /api/pocs` - 获取POC列表
- `GET /api/pocs/{id}` - 获取POC详情
- `POST /api/pocs` - 上传自定义POC
- `PUT /api/pocs/{id}` - 更新POC
- `DELETE /api/pocs/{id}` - 删除POC
- `POST /api/pocs/{id}/execute` - 执行POC验证

### 指纹库接口
- `GET /api/fingerprints` - 获取指纹列表
- `POST /api/fingerprints` - 上传自定义指纹
- `PUT /api/fingerprints/{id}` - 更新指纹
- `DELETE /api/fingerprints/{id}` - 删除指纹

### 节点管理接口
- `GET /api/nodes` - 获取节点列表
- `GET /api/nodes/{id}` - 获取节点详情
- `PUT /api/nodes/{id}` - 更新节点配置
- `DELETE /api/nodes/{id}` - 删除节点
- `GET /api/nodes/{id}/metrics` - 获取节点性能指标

### 报告接口
- `POST /api/reports` - 生成报告
- `GET /api/reports` - 获取报告列表
- `GET /api/reports/{id}` - 获取报告详情
- `GET /api/reports/{id}/export` - 导出报告（PDF/Excel）

### 项目管理接口
- `GET /api/projects` - 获取项目列表
- `GET /api/projects/{id}` - 获取项目详情
- `POST /api/projects` - 创建项目
- `PUT /api/projects/{id}` - 更新项目
- `DELETE /api/projects/{id}` - 删除项目

### 请求/响应格式
```json
// 成功响应
{
  "code": 0,
  "message": "success",
  "data": {...}
}

// 分页响应
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}

// 错误响应
{
  "code": 1,
  "message": "error message",
  "details": {...}
}
```

---

## 7. 前端页面/组件清单

### 主要页面

#### 仪表盘（Dashboard）
- 安全概览：漏洞总数、资产总数、风险评分
- 漏洞趋势图：过去30天的漏洞发现趋势
- 最近任务：列表显示最近执行的扫描任务
- 风险资产排行：按漏洞数和严重程度排序
- 快速操作：创建任务、导入资产、查看报告

#### 资产管理
- 资产列表页：支持搜索、筛选、分页、批量操作
- 资产详情页：显示资产的所有信息、关联的服务、漏洞列表
- 资产分组页：创建、编辑、删除资产分组
- 资产导入页：支持IP段、文件批量导入
- 资产导出页：支持多种格式导出

#### 扫描任务
- 任务列表页：显示所有扫描任务的状态、进度、结果摘要
- 任务创建页：
  - 选择扫描类型（IP端口扫描、URL扫描、POC检测等）
  - 输入扫描范围
  - 关联检测模块（密码破解、目录扫描等）
  - 设置调度规则
- 任务详情页：显示任务详细信息、实时进度条、执行日志
- 任务结果页：汇总任务发现的资产、服务、漏洞

#### 指纹识别
- 指纹库管理页：列表显示所有指纹规则，支持搜索、筛选
- 指纹上传页：支持上传自定义指纹规则
- 指纹匹配结果页：显示指纹识别的匹配结果

#### 漏洞管理
- 漏洞列表页：支持按严重程度、状态、资产等多维度筛选
- 漏洞详情页：显示漏洞信息、影响资产、修复建议
- 漏洞复测页：执行漏洞复测，对比修复前后
- 漏洞统计页：漏洞数量趋势、分布统计等

#### POC管理
- POC库页：列表显示所有可用的POC，支持搜索和分类
- POC上传页：支持上传自定义POC脚本
- POC执行页：选择POC和目标资产执行验证

#### 密码破解
- 字典管理页：管理密码字典
- 破解任务页：创建和管理密码破解任务

#### 项目管理
- 项目列表页：显示所有安全评估项目
- 项目创建页：创建新项目，配置扫描范围和检测模块
- 项目详情页：显示项目信息、关联的资产、任务、漏洞
- 项目报告页：生成项目汇总报告

#### 节点管理
- 节点列表页：显示所有扫描节点的状态、性能指标
- 节点详情页：节点的详细配置和性能监控

#### 报告管理
- 报告列表页：显示已生成的所有报告
- 报告预览页：预览报告内容
- 报告导出页：导出为PDF或Excel格式

#### 用户管理（管理员）
- 用户列表页：管理所有用户
- 用户创建页：创建新用户
- 角色权限管理页：配置角色和权限

### 公共组件
- 顶部导航栏：用户信息、通知、系统设置
- 左侧菜单栏：导航菜单，支持收缩
- 数据表格：通用表格组件，支持排序、筛选、分页
- 图表组件：折线图、柱状图、饼图等
- 弹窗/抽屉：模态对话框、侧滑面板
- 进度条/加载动画：任务执行进度显示
- 标签/徽章：状态标识、分类标签
- 搜索框：全局搜索、字段搜索

---

## 8. 其他要求

### 部署方式

#### Docker容器化
- 将后端、前端、数据库等各组件容器化
- 编写Dockerfile和docker-compose.yml配置文件
- 支持一键启动整个系统

#### 多节点部署架构
- **中心控制台**：主控制节点，负责任务分发、数据汇总、报告生成
- **扫描节点**：分布在内网各处，执行具体的扫描任务，支持水平扩展
- **数据库集群**：PostgreSQL主从复制，确保高可用性
- **缓存集群**：Redis集群，支持高并发访问

#### Kubernetes编排（可选）
- 支持在Kubernetes环境中部署
- 编写Helm Charts配置
- 自动扩容/缩容

### 测试要求

#### 单元测试
- 后端核心业务逻辑的单元测试，覆盖率 ≥ 80%
- 前端组件单元测试

#### 集成测试
- API集成测试
- 工具集成测试（确保与afrog、nuclei等工具正常集成）

#### 系统测试
- 端到端的功能测试
- 性能测试（并发扫描能力、响应时间等）
- 安全渗透测试

### 文档要求

#### 系统设计文档
- 系统架构设计
- 数据库设计
- API设计文档
- 工具集成指南

#### 部署文档
- Docker部署指南
- Kubernetes部署指南
- 系统初始化和配置说明
- 故障排查指南

#### 用户手册
- 系统使用说明
- 常见问题解答
- 视频教程

#### 开发文档
- 开发环境搭建指南
- 代码规范
- 模块开发指南
- 插件开发指南

#### 运维文档
- 系统监控和告警配置
- 备份和恢复策略
- 性能优化建议
- 扩容指南

---

## 9. 集成工具详解

### afrog
- **用途**：综合漏洞扫描器
- **集成方式**：调用其CLI接口，传入扫描目标和参数
- **输出处理**：解析JSON格式的扫描结果，存储到数据库

### dddd
- **用途**：DNS和子域名扫描
- **集成方式**：通过API或CLI接口调用
- **输出处理**：提取子域名和IP地址，补充资产信息

### fscan
- **用途**：内网扫描工具，快速发现资产
- **集成方式**：调用CLI接口，传入IP段范围
- **输出处理**：解析扫描结果，导入资产表

### nuclei
- **用途**：POC框架，支持模板化的漏洞验证
- **集成方式**：调用CLI接口，传入POC模板和目标
- **输出处理**：解析YAML格式的POC模板，执行验证，记录结果

### dirsearch
- **用途**：Web目录扫描工具
- **集成方式**：调用CLI接口，传入目标URL和字典
- **输出处理**：解析发现的目录和文件，存储为URL资产

---

## 10. 系统架构设计

### 整体架构
```
┌─────────────────────────────────────────────────────────────────┐
│                        前端应用层                                │
│                  (React + TypeScript + Ant Design)               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                    ┌──────┴───────┐
                    │              │
        ┌───────────▼──────┐  ┌────▼──────────┐
        │   API Gateway    │  │  WebSocket    │
        │  (认证/鉴权)     │  │  (实时推送)   │
        └───────────┬──────┘  └────┬──────────┘
                    │              │
        ┌───────────┴──────────────┴────────┐
        │                                   │
    ┌───▼────────────────────┐   ┌────────▼─────┐
    │  后端服务层            │   │  任务队列    │
    │  (FastAPI)             │   │  (Celery+    │
    │  - 用户管理            │   │   Redis)     │
    │  - 资产管理            │   └────┬─────────┘
    │  - 任务管理            │        │
    │  - 漏洞管理            │   ┌────▼────────┐
    │  - 报告生成            │   │  扫描节点   │
    └───┬────────────────────┘   │  (分布式)   │
        │                         │  - afrog    │
        │                         │  - nuclei   │
    ┌───┴─────────────────────┐  │  - fscan    │
    │   数据存储层            │  │  - dirsearch│
    │ - PostgreSQL (主数据)   │  └─────┬──────┘
    │ - Redis (缓存+队列)     │        │
    │ - InfluxDB (时序数据)   │   ┌────▼──────┐
    │ - Elasticsearch (全文)  │   │  工具集成 │
    └───────────────────────┘   │  引擎      │
                                 └───────────┘
```

### 分层设计

#### 表现层
- 前端UI框架
- 组件库和样式库
- 状态管理

#### 业务逻辑层
- 用户认证和授权
- 资产生命周期管理
- 扫描任务编排
- 漏洞分析和关联

#### 集成层
- 工具调用和参数转换
- 结果解析和标准化
- 异步任务分发

#### 数据层
- ORM映射（SQLAlchemy）
- 缓存策略
- 查询优化

---

## 11. 系统工作流程

### 典型的漏洞发现工作流

```
1. 用户导入资产
   ↓
2. 创建扫描任务（选择扫描类型和关联模块）
   ↓
3. 系统接收任务，生成扫描计划
   ↓
4. 任务分发到适当的扫描节点
   ↓
5. 扫描节点执行多步骤扫描：
   - 端口扫描（fscan/nmap）
     ↓
   - 服务识别
     ↓
   - 指纹识别（52000+指纹库）
     ↓
   - 自动触发POC检测（基于识别结果）
     ↓
   - 自动触发密码破解（如发现SSH/FTP等）
     ↓
   - 自动执行目录扫描（如发现Web服务）
   ↓
6. 实时推送扫描进度到前端（WebSocket）
   ↓
7. 汇总扫描结果，存储到数据库
   ↓
8. 去重、聚合漏洞，生成漏洞列表
   ↓
9. 前端展示漏洞，用户可进行标记、复测等操作
   ↓
10. 生成安全评估报告
```

### 漏洞复测工作流

```
1. 用户标记漏洞为"已修复"
   ↓
2. 点击"复测"按钮
   ↓
3. 系统重新执行相应的POC检测
   ↓
4. 对比修复前后的结果
   ↓
5. 生成复测报告
   ↓
6. 更新漏洞状态为"已验证修复"或"仍然存在"
```

---

## 12. 核心功能模块详细设计

### 12.1 任务调度引擎

#### 任务流程
```python
class TaskOrchestrator:
    def create_task(self, task_config):
        """创建任务"""
        # 验证配置
        # 生成子任务
        # 分发到队列
        pass
    
    def execute_scan_pipeline(self, target, modules):
        """执行扫描管道"""
        # 1. 端口扫描
        ports = await port_scan(target)
        
        # 2. 服务识别
        services = await service_identify(target, ports)
        
        # 3. 指纹识别
        fingerprints = await fingerprint_match(services)
        
        # 4. 自动触发关联检测
        if 'poc' in modules and fingerprints:
            poc_results = await trigger_poc_detection(fingerprints)
        
        if 'weak_password' in modules and vulnerable_services(services):
            password_results = await trigger_password_crack(services)
        
        if 'directory_scan' in modules and web_services(services):
            directory_results = await trigger_directory_scan(services)
        
        return aggregate_results(ports, services, fingerprints, ...)
```

#### 关键特性
- 支持管道化执行，上游的输出是下游的输入
- 支持并行化处理多个目标
- 支持动态调整扫描参数
- 支持任务暂停和恢复

### 12.2 指纹识别引擎

#### 性能优化
```python
class FingerprintMatcher:
    def __init__(self):
        # 预加载52000+条指纹规则
        self.fingerprints = self.load_fingerprints()
        # 构建索引（按服务类型、产品名等）
        self.build_indexes()
        # 编译正则表达式，缓存预编译结果
        self.compiled_patterns = {}
    
    async def match_batch(self, targets, batch_size=100):
        """批量匹配指纹"""
        # 使用异步IO并行处理
        # 预估处理1万个Web系统耗时8-10分钟
        tasks = []
        for target in targets:
            tasks.append(self.match_single(target))
        
        results = await asyncio.gather(*tasks)
        return results
    
    def match_single(self, target):
        """单个目标匹配"""
        # 从HTTP响应头、页面内容、技术栈特征等多维度识别
        candidates = []
        for fp in self.fingerprints:
            if self.check_match(target, fp):
                candidates.append((fp, confidence))
        return sorted(candidates, key=lambda x: x[1], reverse=True)
```

#### 指纹更新
- 支持导入新的指纹规则
- 支持从FOFA、Shodan等数据源自动更新
- 支持社区贡献的指纹规则

### 12.3 POC管理和执行

#### POC格式支持
```yaml
# Nuclei格式示例
id: cve-2021-xxxx
info:
  name: Vulnerable App RCE
  severity: high
  cves:
    - CVE-2021-xxxx

requests:
  - method: GET
    path: /api/vulnerable-endpoint
    headers:
      Authorization: "Bearer {{token}}"
    matchers:
      - type: status
        status:
          - 200
      - type: word
        words:
          - "success"
```

#### POC执行
```python
class POCExecutor:
    async def execute_poc(self, poc_id, targets, parameters=None):
        """执行POC验证"""
        poc = self.load_poc(poc_id)
        
        # 支持多种执行方式
        if poc.type == 'nuclei':
            results = await self.execute_nuclei(poc, targets, parameters)
        elif poc.type == 'custom':
            results = await self.execute_custom_script(poc, targets, parameters)
        elif poc.type == 'metasploit':
            results = await self.execute_metasploit(poc, targets, parameters)
        
        # 标准化结果格式
        return self.normalize_results(results)
    
    async def batch_execute_poc(self, pocs, target):
        """批量执行POC"""
        # 根据目标的服务和指纹自动匹配相关POC
        matching_pocs = self.match_pocs_by_fingerprint(target)
        
        results = []
        for poc in matching_pocs:
            result = await self.execute_poc(poc.id, [target])
            results.append(result)
        
        return results
```

### 12.4 弱口令破解

#### 集成Hydra/Medusa
```python
class PasswordCracker:
    def create_task(self, target, protocol, username_list, password_list):
        """创建密码破解任务"""
        # 支持的协议：ssh, ftp, telnet, http, smb, mysql等
        
        config = {
            'target': target,
            'protocol': protocol,
            'username_file': self.create_temp_file(username_list),
            'password_file': self.create_temp_file(password_list),
            'thread_count': 16,  # 可配置的并发数
            'timeout': 30
        }
        
        # 调用hydra/medusa执行
        result = await self.execute_hydra(config)
        
        # 保存发现的凭证
        for cred in result.credentials:
            self.save_credential(target, cred)
    
    def get_common_usernames(self, service_type):
        """根据服务类型获取常用用户名"""
        return {
            'ssh': ['root', 'admin', 'user', 'test'],
            'ftp': ['admin', 'ftp', 'user', 'test'],
            'mysql': ['root', 'admin', 'mysql'],
            # ...
        }
    
    def get_common_passwords(self, service_type):
        """根据服务类型获取常用密码"""
        return {
            'ssh': ['123456', 'password', 'admin123', 'root', '123456789'],
            'ftp': ['123456', 'password', 'admin', 'ftp'],
            # ...
        }
```

---

## 13. 实现路线图

### 第一阶段：核心功能（第1-2月）
- [ ] 用户管理和认证系统
- [ ] 资产导入和管理
- [ ] 端口扫描和服务识别
- [ ] 指纹识别引擎
- [ ] 基础的前端页面

### 第二阶段：高级功能（第3-4月）
- [ ] POC管理和执行
- [ ] 漏洞管理和复测
- [ ] 弱口令破解
- [ ] 目录扫描
- [ ] 报告生成

### 第三阶段：分布式和优化（第5-6月）
- [ ] 多节点部署架构
- [ ] 任务分布式执行
- [ ] 性能优化
- [ ] 安全加固
- [ ] 完整的文档和测试

### 第四阶段：运维和扩展（第7个月+）
- [ ] 系统监控和告警
- [ ] 插件系统
- [ ] 更多工具集成
- [ ] 生态建设

---

## 14. 关键性能指标（KPI）

| 指标 | 目标值 | 说明 |
|------|-------|------|
| 指纹识别效率 | 1万/8-10分钟 | 1万个Web系统指纹识别耗时 |
| API响应时间 | <500ms | 平均响应延迟 |
| 系统可用性 | 99.5% | 月度可用时间占比 |
| 并发扫描任务数 | ≥100 | 支持的最大并发任务 |
| 数据库查询时间 | <1s | 资产列表查询耗时 |
| 前端加载时间 | <3s | 首屏加载时间 |
| 漏洞告警延迟 | <5分钟 | 从发现到告警的延迟 |

---

## 15. 成本预估

### 开发成本
- 后端开发：600小时
- 前端开发：400小时
- 测试和文档：200小时
- 总计：约4-6个月，3-5人团队

### 基础设施成本（月度）
- 服务器：3台（1个主节点+2个扫描节点）
- 数据库和缓存服务
- 存储空间
- 网络带宽

### 许可证成本
- 开源项目为主（无许可费用）
- 可选的商业工具集成

---

## 16. 风险和缓解措施

### 风险1：扫描对网络的影响
**风险**：大规模扫描可能导致网络拥塞或误触发防火墙
**缓解**：
- 支持速率限制和流量控制
- 支持按时间段调度扫描
- 提供扫描前的风险评估

### 风险2：POC的准确性和更新
**风险**：POC库的准确性和及时性难以保证
**缓解**：
- 建立POC质量评审机制
- 支持社区反馈和改进
- 定期更新和维护POC库

### 风险3：大规模数据处理能力
**风险**：处理数百万资产和漏洞的性能问题
**缓解**：
- 分布式架构设计
- 数据库优化（分表分库）
- 使用时序数据库处理大量历史数据

### 风险4：安全性和数据保护
**风险**：系统本身被攻击、数据泄露
**缓解**：
- 严格的访问控制和审计日志
- 数据加密存储和传输
- 定期的安全审计和渗透测试

---

## 17. 成功指标

系统成功部署和运行的标志：
- ✅ 能够在30分钟内完成1000个IP的资产发现
- ✅ 指纹识别准确率 ≥ 95%
- ✅ POC验证准确率 ≥ 90%
- ✅ 系统支持100+并发扫描任务
- ✅ 生成的报告被安全团队认可并使用
- ✅ 帮助企业发现和修复至少100+个真实漏洞

---

## 附录：术语表

| 术语 | 定义 |
|------|------|
| 资产 | 企业内网中的一台计算机、服务器、网络设备等 |
| 指纹 | 用于识别特定软件、系统或服务的特征信息 |
| POC | Proof of Concept，漏洞验证代码 |
| 漏洞 | 系统或应用中存在的安全缺陷或薄弱点 |
| CVSS | Common Vulnerability Scoring System，漏洞评分体系 |
| 扫描节点 | 执行具体扫描任务的分布式节点 |
| 字典 | 用于密码破解的用户名/密码列表 |
| 修复验证 | 在漏洞修复后重新执行检测以验证修复有效性 |