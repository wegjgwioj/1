# Windows 本地自举方案设计

**日期：** 2026-04-14

## 背景

当前仓库已经具备较完整的业务功能、预测链路和前后端启动脚本，但推荐启动路径仍偏向 `Docker + 容器数据库`。这与当前交付目标不一致，因为最终要提交到 GitHub，供其他同学在 **Windows、本机无 Docker** 的前提下，完成环境配置后通过一键脚本直接构建并启动项目。

现状中的主要问题有：

1. `README.md` 的主路径仍以 Docker 为核心，克隆后不利于直接上手。
2. 现有 `bin/start_backend.ps1` 和 `bin/start_project.ps1` 已经能启动服务，但不能完成首次本地自举。
3. 根目录 `.env.example` 与前端 `.env.example` 还没有完全按“Windows 本地 MySQL + 可选 Redis”来表述。
4. 数据库初始化既有 `init.py`/`util.sqlinit.py`，也有完整 SQL dump，但没有统一成“首次使用者可直接执行”的流程。
5. `db/init/002_feature_patch.sql` 和 `004_prediction_upgrade.sql` 不是幂等脚本，不适合被新的引导脚本无脑重复执行。

## 目标

本轮要把项目整理为一套清晰、稳定、可复现的 Windows 本地启动方案：

- 新用户 `clone` 仓库后，只要本机提前装好 `Python 3.11`、`Node.js`、`MySQL`，就能执行一条 PowerShell 脚本完成初始化。
- 首次初始化能够自动创建 `.venv`、安装依赖、生成环境变量文件、准备前端依赖、初始化数据库并补齐业务表结构。
- Redis 作为可选能力，不再阻塞系统启动；即使 Redis 未安装或鉴权失败，系统也能回退本地缓存继续运行。
- 后续启动流程保持简单：首次执行 `bootstrap_local.ps1`，以后执行 `start_project.ps1`。

## 方案对比

### 方案 A：继续以 Docker 为主，只补文档

优点：

- 改动最少。
- 环境一致性较高。

缺点：

- 与“目标机器没有 Docker”的约束冲突。
- 用户仍要自己理解 Docker、容器端口、数据卷和宿主机映射。
- 不满足本轮 GitHub 交付要求。

### 方案 B：纯 PowerShell 自举，但数据库导入全部依赖 `mysql` 命令行

优点：

- 启动路径直观，脚本文件少。
- 只要本机装了 MySQL Server 和客户端就可以完成导入。

缺点：

- 不同 Windows 安装路径下，`mysql.exe` 不一定进入 `PATH`。
- 遇到自定义库名时，需要额外处理 SQL 中固定的 `DROP DATABASE / CREATE DATABASE / USE` 语句。
- 对错误提示和幂等处理不够友好。

### 方案 C：PowerShell 总控 + Python 数据库辅助脚本

优点：

- 更容易复用项目现有的 Python 依赖和配置读取逻辑。
- 可以在导入 SQL 前动态替换固定库名，兼容用户自定义 `DB_NAME`。
- 可以更细致地处理“数据库已存在/首次导入/跳过导入/后续补 schema”的分支。
- 便于写自动化测试，适合稳定交付。

缺点：

- 需要新增一个 Python 辅助脚本。
- 启动链路比纯 PowerShell 略复杂。

**推荐：** 采用方案 C。它最符合当前项目基础，也最适合做成“别人 clone 后按说明即可成功”的稳定方案。

## 设计

### 1. 脚本结构

新增以下入口：

- `bin/bootstrap_local.ps1`
- `bin/bootstrap_local_db.py`

并继续复用：

- `bin/start_backend.ps1`
- `bin/start_project.ps1`

职责划分如下：

- `bootstrap_local.ps1`
  - 检查 `Python / Node.js / npm`
  - 创建 `.venv`
  - 安装后端依赖
  - 安装前端依赖
  - 复制 `.env.example -> .env`
  - 复制 `templates/front/admin/.env.example -> templates/front/admin/.env`
  - 探测 MySQL / Redis 环境信息
  - 调用 `bootstrap_local_db.py` 处理数据库
  - 执行 `migrate --fake-initial`
  - 执行 `sync_feature_schema`
  - 可选执行 `prepare_demo_data`
  - 最后调用 `start_project.ps1`

- `bootstrap_local_db.py`
  - 读取 `.env`/`config.ini`
  - 连接 MySQL
  - 检查目标库是否存在
  - 如不存在，则基于 `db/diandong5k56la1f.sql` 创建数据库并导入基础数据
  - 如存在，则跳过基础导入，仅提示后续通过 Django 命令补齐结构

### 2. 数据库初始化策略

本轮不把 `db/init/002_feature_patch.sql` 与 `004_prediction_upgrade.sql` 直接纳入脚本强执行，而采用“基础 dump + Django 幂等补丁”的组合：

1. 首次新库：
   - 导入 `db/diandong5k56la1f.sql`
2. 无论新库还是旧库：
   - `python manage.py migrate --fake-initial`
   - `python manage.py sync_feature_schema`
3. 如用于答辩展示：
   - 可选执行 `python manage.py prepare_demo_data`

这样做的原因是：

- `sync_feature_schema()` 已具备幂等能力，适合旧库补字段/补表。
- `prepare_demo_data()` 负责演示数据整理，也具备重复执行能力。
- 避免非幂等 SQL 重复执行导致“字段已存在”“表已存在”“重复修改”的问题。

### 3. 自定义数据库名兼容

`db/diandong5k56la1f.sql` 内部固定写死了 `diandong5k56la1f`，因此 `bootstrap_local_db.py` 需要在导入前对以下语句进行替换：

- `DROP DATABASE IF EXISTS`
- `CREATE DATABASE`
- `USE`
- 顶部注释中的当前数据库名说明

替换目标为当前运行时解析到的 `DB_NAME`。这样既能保留现有 SQL 文件作为基础数据来源，又不会把数据库名绑定死。

### 4. 环境变量约定

这次统一按“本地部署优先”来组织环境变量：

- 后端/数据库：
  - `DB_HOST`
  - `DB_PORT`
  - `DB_NAME`
  - `DB_USER`
  - `DB_PASSWORD`
  - `DB_CHARSET`
- 服务访问：
  - `APP_BACKEND_HOST`
  - `APP_BACKEND_PORT`
  - `APP_FRONTEND_PORT`
  - `VITE_API_BASE_URL`
- Redis：
  - `REDIS_HOST`
  - `REDIS_PORT`
  - `REDIS_PASSWORD`
  - `REDIS_DB`

其中 Redis 明确标注为“可选”。如果没有本地 Redis，脚本只给出提示，不中断流程。

### 5. README 主路径调整

`README.md` 将改成以下结构：

1. 先写 Windows 本地启动前提
2. 再写首次执行 `bootstrap_local.ps1`
3. 再写后续执行 `start_project.ps1`
4. 再补充训练命令、测试命令、常见问题
5. Docker 方案降级为“可选补充路径”，不再作为主文档流程

这样用户克隆仓库后，直接看前半部分即可完成运行。

## 测试策略

先在 `util/tests_startup_scripts.py` 补失败测试，覆盖以下要求：

- `bin/bootstrap_local.ps1` 必须存在
- `bin/bootstrap_local_db.py` 必须存在
- `bootstrap_local.ps1` 必须包含：
  - `.venv`
  - `pip install -r requirements.txt`
  - `npm install`
  - `.env.example`
  - `migrate --fake-initial`
  - `sync_feature_schema`
  - `start_project.ps1`
- `README.md` 必须把 `bootstrap_local.ps1` 写为首要启动入口

完成后再实现脚本，最后运行：

- `.\.venv\Scripts\python.exe -m unittest util.tests_configread util.tests_startup_scripts -v`
- `.\.venv\Scripts\python.exe manage.py check`

## 风险与处理

### 1. 用户本机未安装 MySQL

本轮不负责自动安装 MySQL Server。本地自举的边界是：脚本自动检查并给出明确提示，但不代替系统级安装。

### 2. 用户本机 `mysql.exe` 不在 PATH

本方案优先使用 Python 连接数据库并执行 SQL，降低对外部客户端路径的依赖。

### 3. 工作区已有未提交修改

这轮只增量修改启动链路、配置示例、README、测试与文档，不回退用户已有前端改动。

## 交付结果

完成后，仓库应具备以下形态：

- Windows 本地首次初始化只需执行一次 `bootstrap_local.ps1`
- 后续运行只需执行 `start_project.ps1`
- README 对新用户友好，默认不要求 Docker
- 数据库初始化不会重复硬执行非幂等 SQL
- 启动链路、环境变量与测试约束一致，可作为 GitHub 交付版本
