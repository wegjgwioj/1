# Windows 本地自举方案实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标：** 把项目整理成适合提交 GitHub 的 Windows 本地自举版本，让别人 `clone` 后在无 Docker 环境下也能通过一键脚本完成初始化和启动。

**架构：** 采用 `PowerShell 总控脚本 + Python 数据库辅助脚本 + 现有 Django 启动脚本复用` 的路径。首次初始化负责依赖安装、环境文件生成、数据库导入与 Django 补丁；后续运行继续走已有前后端启动脚本。

**技术栈：** PowerShell、Python 3.11、Django、PyMySQL、Vue 3 + Vite、MySQL、可选 Redis、Windows 本地环境。

---

### 任务 1：补齐设计文档与计划文档

**文件：**
- 新建：`docs/plans/2026-04-14-windows-local-bootstrap-design.md`
- 新建：`docs/plans/2026-04-14-windows-local-bootstrap.md`

**步骤 1：写入设计文档**

要求包含：

- 为什么不用 Docker 作为主路径
- 为什么采用 PowerShell + Python 辅助脚本
- 为什么不直接重复执行 `db/init/*.sql`

**步骤 2：写入实施计划**

要求明确文件路径、测试命令和最终验证命令。

### 任务 2：先扩展启动脚本测试

**文件：**
- 修改：`util/tests_startup_scripts.py`

**步骤 1：先写失败测试**

新增断言：

- `bin/bootstrap_local.ps1` 存在
- `bin/bootstrap_local_db.py` 存在
- `bootstrap_local.ps1` 包含：
  - `.venv`
  - `pip install -r requirements.txt`
  - `npm install`
  - `.env.example`
  - `migrate --fake-initial`
  - `sync_feature_schema`
  - `start_project.ps1`
- `README.md` 提到 `bootstrap_local.ps1`

**步骤 2：运行测试，确认按预期失败**

运行：`.\.venv\Scripts\python.exe -m unittest util.tests_startup_scripts -v`

预期：因为脚本尚未创建或内容不足而失败。

### 任务 3：实现数据库自举辅助脚本

**文件：**
- 新建：`bin/bootstrap_local_db.py`

**步骤 1：实现配置读取**

复用 `util.configread.config_read()`，并补充从 `.env` 读取数据库参数。

**步骤 2：实现首次导库逻辑**

行为要求：

- 若数据库不存在，则创建数据库并导入 `db/diandong5k56la1f.sql`
- 导入前将固定库名替换成运行时 `DB_NAME`

**步骤 3：实现幂等行为**

行为要求：

- 若数据库已存在，则跳过基础 dump 导入
- 只输出提示，由后续 Django 命令补齐结构

### 任务 4：实现总入口自举脚本

**文件：**
- 新建：`bin/bootstrap_local.ps1`

**步骤 1：实现环境检查**

检查：

- `py` 或 `python`
- `node`
- `npm`

对缺失项给出清晰错误提示。

**步骤 2：实现依赖安装**

执行：

- 创建 `.venv`
- `pip install -r requirements.txt`
- `npm install`

**步骤 3：实现环境文件生成**

行为要求：

- `.env` 不存在时从 `.env.example` 复制
- `templates/front/admin/.env` 不存在时从其示例文件复制

**步骤 4：串起数据库初始化与 Django 命令**

按顺序执行：

- `bootstrap_local_db.py`
- `manage.py migrate --fake-initial`
- `manage.py sync_feature_schema`
- 可选 `manage.py prepare_demo_data`

**步骤 5：最后调用启动脚本**

执行：`powershell -ExecutionPolicy Bypass -File .\bin\start_project.ps1`

### 任务 5：调整环境变量示例

**文件：**
- 修改：`.env.example`
- 修改：`templates/front/admin/.env.example`

**步骤 1：统一变量命名与注释**

要求说明：

- 本地 MySQL 是主路径
- Redis 为可选
- 默认前端请求地址如何与后端端口对应

**步骤 2：保持与现有代码兼容**

避免引入新的命名而不兼容当前 `config_read()` 和前端 Vite 配置。

### 任务 6：改造 README 主路径

**文件：**
- 修改：`README.md`

**步骤 1：把 Windows 本地部署写成主流程**

至少包含：

1. 运行前提
2. 首次执行 `bootstrap_local.ps1`
3. 后续执行 `start_project.ps1`
4. 训练命令
5. 测试命令
6. 常见问题

**步骤 2：把 Docker 降级为补充说明**

不再把 Docker 写成推荐默认路径。

### 任务 7：运行完整验证

**文件：**
- 无

**步骤 1：运行脚本测试**

运行：`.\.venv\Scripts\python.exe -m unittest util.tests_startup_scripts -v`

预期：全部通过。

**步骤 2：运行配置与启动相关测试**

运行：`.\.venv\Scripts\python.exe -m unittest util.tests_configread util.tests_startup_scripts -v`

预期：全部通过。

**步骤 3：运行 Django 检查**

运行：`.\.venv\Scripts\python.exe manage.py check`

预期：检查通过。

**步骤 4：必要时补充静态核对**

核对 `README.md`、`.env.example`、`templates/front/admin/.env.example` 与脚本描述保持一致。
