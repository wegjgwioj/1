# 电动汽车行车日志系统

这是一个基于 `Django + Vue 3` 的电动汽车行车日志与电池预测系统，当前仓库已经整理为 **Windows 本地自举优先** 的交付形态。默认不要求 Docker，适合直接提交到 GitHub 后由别人 `clone` 下来在本机完成构建和启动。

## 当前已具备的核心功能

- 行车日志管理、筛选、导入与展示
- 电池寿命/能耗预测工作台
- ML 主模型训练与评估
- DL 对比实验链路
- NASA 公开电池寿命数据集 SOH/RUL 实验链路
- 行车日志收藏、评论、管理员回复
- 车型知识采集与知识库页面

## 目录说明

- `main/`：Django 业务逻辑与管理命令
- `templates/front/admin/`：Vue 3 管理端
- `db/`：MySQL 基础 SQL 和补充脚本
- `bin/`：Windows 启动与自举脚本
- `artifacts/`：模型与评估产物
- `docs/`：论文、规划和讲解材料

## Windows 本地启动

### 1. 运行前提

请先在 Windows 本机安装好以下环境：

- `Python 3.11`
- `Node.js 18+`
- `MySQL 5.7/8.0`
- `Redis` 可选，不装也能运行

建议确认这些命令可以直接在 PowerShell 中使用：

```powershell
py -3.11 --version
node --version
npm --version
```

### 2. 首次初始化

首次 `clone` 仓库后，在项目根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\bin\bootstrap_local.ps1
```

这个脚本会自动完成：

- 创建 `.venv`
- 安装 `requirements.txt`
- 安装前端 `npm` 依赖
- 生成根目录 `.env`
- 生成前端 `.env`
- 初始化本地 MySQL 数据库
- 执行 `migrate --fake-initial`
- 执行 `sync_feature_schema`
- 最后调用 `start_project.ps1` 启动前后端

如果你希望首次初始化时顺带整理答辩演示数据，可以执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\bin\bootstrap_local.ps1 -PrepareDemoData
```

### 3. 后续启动

首次初始化完成后，后续只需要执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\bin\start_project.ps1
```

它会：

- 在新 PowerShell 窗口里启动 Django 后端
- 在当前窗口里启动 Vue 前端

默认地址：

- 前端：`http://127.0.0.1:8081`
- 后端：`http://127.0.0.1:8082`

如果你只想单独启动后端，可执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\bin\start_backend.ps1
```

## 环境变量说明

根目录 `.env.example` 已按本地部署整理，常用变量如下：

- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_CHARSET`
- `APP_BACKEND_HOST`
- `APP_BACKEND_PORT`
- `APP_FRONTEND_PORT`
- `VITE_API_BASE_URL`
- `REDIS_HOST`
- `REDIS_PORT`
- `REDIS_PASSWORD`
- `REDIS_DB`

说明：

- Django 会优先读取 `.env`，不足时再回退到 `config.ini`
- Redis 在本项目中是可选组件；未安装或认证失败时，系统会自动回退到本地缓存
- 前端 `.env` 主要用于本地开发兜底，默认会请求 `VITE_API_BASE_URL`

## 数据库初始化策略

首次本地自举时，脚本会使用 `bin/bootstrap_local_db.py` 处理数据库：

- 若数据库不存在，则导入 `db/diandong5k56la1f.sql`
- 若数据库已存在，则跳过基础导入
- 无论是否首次导入，后续都会执行：
  - `python manage.py migrate --fake-initial`
  - `python manage.py sync_feature_schema`

这样做是为了避免重复执行 `db/init/002_feature_patch.sql`、`004_prediction_upgrade.sql` 这类非幂等脚本。

## 训练与实验命令

### 机器学习主模型

```powershell
.\.venv\Scripts\python.exe manage.py train_ml_models
.\.venv\Scripts\python.exe manage.py evaluate_ml_models
```

### 深度学习对比链路

```powershell
.\.venv\Scripts\python.exe manage.py prepare_sequence_data
.\.venv\Scripts\python.exe manage.py train_dl_model
.\.venv\Scripts\python.exe manage.py compare_models
```

### NASA SOH/RUL 实验

```powershell
.\.venv\Scripts\python.exe manage.py prepare_nasa_battery_dataset --source-dir datasets\nasa_battery --download
.\.venv\Scripts\python.exe manage.py train_nasa_battery_models
```

说明：

- 前端预测工作台继续以 ML 结果为主展示链路
- DL 是对比实验链路，不替代主业务预测结果
- 如果当前环境未安装 `torch`，系统会回退到轻量神经网络近似实现
- NASA 实验产物默认输出到 `artifacts/battery_life/`

## 常用验证命令

```powershell
.\.venv\Scripts\python.exe -m unittest util.tests_configread util.tests_startup_scripts -v
.\.venv\Scripts\python.exe manage.py check
cd templates/front/admin
npm run build
```

## 车型知识采集说明

当前项目中的“爬虫”已经整理为真实可演示的车型知识采集功能：

- 采集对象：`vehiclemodel` 对应的公开车型知识
- 入库位置：`vehicleknowledge` 表
- 前端入口：
  - 行车日志列表里的 `采集车型知识`
  - 车型知识库页里的 `批量采集` / `重新采集`

说明：

- 它用于补全公开车型资料，不用于伪造原始行车遥测日志
- 答辩前可执行 `python manage.py prepare_demo_data` 清理旧采集残留并标准化演示车型

## Docker 补充说明

仓库仍保留了 `docker-compose.yml` 和 Docker 相关文件，但这条路径现在只是补充方案，不再是默认推荐方式。当前主文档与一键脚本都以 **Windows 本地部署** 为准。
