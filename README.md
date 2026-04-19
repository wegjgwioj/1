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
- 用户角色与管理员角色分权访问

## 目录说明

- `main/`：Django 业务逻辑与管理命令
- `templates/front/admin/`：Vue 3 管理端
- `db/`：MySQL 基础 SQL 和补充脚本
- `bin/`：Windows 启动与自举脚本
- `artifacts/`：模型与评估产物
- `docs/`：论文、规划和讲解材料

## 项目学习资料

如果你是第一次接触这个项目，建议按下面顺序阅读 `docs/` 中的讲解稿：

1. `项目导读.md`
2. `系统架构讲解.md`
3. `后端实现讲解.md`
4. `前端实现讲解.md`
5. `预测与实验讲解.md`
6. `部署与运行讲解.md`
7. `测试与答辩讲解.md`
8. `论文写作讲解.md`
9. `相关文献整理.md`

这组文档以“学习路径 + 论文主线”为组织方式，重点讲清项目思路、系统架构、实现取舍和答辩表达，代码路径作为辅助说明。

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
- 后端 API 基址：`http://127.0.0.1:8082`

如果你只想单独启动后端，可执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\bin\start_backend.ps1
```

如果你本机已经准备好了 Docker 中的 MySQL/Redis，也可以让启动脚本顺带拉起容器依赖：

```powershell
powershell -ExecutionPolicy Bypass -File .\bin\start_project.ps1 -StartDockerServices
```

## 默认演示账号

数据库初始化完成后，默认可直接使用以下账号登录：

- 管理员：`admin / admin`
- 用户：`21 / 123456`

补充说明：

- SQL 中还预置了多个普通用户账号：`22`、`23`、`24`、`25`、`26`、`27`、`28`
- 上述普通用户默认密码均为：`123456`
- 管理员用于数据维护、评论回复、采集和后台管理
- 用户用于列表浏览、收藏、评论和预测分析演示

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

## 登录与使用说明

- 浏览器入口统一从前端地址进入：`http://127.0.0.1:8081`
- 不要直接访问 `8082` 作为页面入口，`8082` 是 Django API 服务端口
- 登录成功后默认会进入系统首页/看板页，再通过左侧菜单进入业务页面
- 用户角色和管理员角色看到的按钮不同，这是权限过滤后的正常行为

如果刚更新过前端代码，旧标签页里还残留了历史登录态或旧脚本缓存，可能出现页面状态异常。此时建议：

- 先退出登录，再重新登录
- 或直接执行一次 `Ctrl + F5` 强制刷新
- 如仍异常，可清理浏览器 `localStorage` 后重试

## 评论与回复功能说明

当前评论模块已经和 `drivinglog` 行车日志记录建立关联，完整链路如下：

1. 用户进入“行车日志”列表。
2. 在某条日志上点击“评论”。
3. 在评论表单中填写“评论内容”并提交。
4. 系统按 `refid` 关联到对应行车日志，同时同步该日志的评论数量 `discussnum`。
5. 管理员进入“评论反馈”列表后，可以查看评论并进行回复。

当前评论字段展示规则：

- `vehicleinfo`：显示评论关联的车辆编号、车辆型号、行驶路线摘要
- `replydisplay`：展示格式化后的回复记录
- 未回复时，前端默认显示：`未回复`
- 管理员回复后，会按“昵称：内容”的格式展示回复记录

权限规则：

- 普通用户只能查看自己的评论记录
- 普通用户不能修改、删除评论反馈记录
- 管理员可以查看全部评论、执行回复和删除

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
.\.venv\Scripts\python.exe manage.py test main.tests.DiscussFlowTest --keepdb -v 2
cd templates/front/admin
node --test tests\app-bootstrap.test.mjs tests\user-role-actions.test.mjs
npm run build
```

这些命令分别用于验证：

- 环境变量与启动脚本
- Django 配置与路由注册
- 评论/回复后端链路
- 前端权限按钮与应用启动链路
- Vue 生产构建是否正常

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

## 常见问题

### 1. 打开 `http://127.0.0.1:8081` 后先看到看板而不是登录页

这是因为浏览器里还保留了之前的登录状态。系统检测到已有有效会话时，会直接进入首页而不是再次显示登录页。

处理方式：

- 先点击退出登录
- 或清理浏览器本地存储后重新访问
- 如果只是刚切换代码版本，执行一次 `Ctrl + F5` 即可

### 2. 登录后页面按钮没反应

当前版本已经修复了一个前端重复挂载导致的登录后页面失活问题。若你仍遇到这个现象，通常是旧浏览器缓存未清掉：

- 先强制刷新页面
- 再重新登录
- 确认前端运行端口是 `8081`
- 确认后端 API 基址是 `8082`

### 3. 看不到评论输入或回复状态

请确认当前使用的是最新前端代码。当前版本中：

- 用户在“行车日志”列表中通过“评论”按钮提交评论
- 评论表单中的“评论内容”使用多行文本输入框
- 评论反馈列表会显示关联行车日志摘要和“未回复/已回复”状态
