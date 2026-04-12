# 电动汽车行车日志系统

这个仓库的推荐运行方式已经统一为：

- `MySQL + Redis` 运行在 Docker 里
- Django 后端运行在宿主机
- Vue 3 管理前端运行在宿主机

这样做的目的只有一个：尽量保证换电脑后环境一致、启动步骤固定、数据库不再依赖“某个人本机刚好装了什么”。

另外，本次已经顺手做了基础安全收口：

- 移除了前端入口对外部 CDN 脚本的依赖，改为本地 npm 包加载
- 移除了支付宝模板残留与仓库内的支付宝密钥文件
- 移除了前端明文 AI key，并将邮件凭据改为环境变量读取
- 初始化 SQL 中的第三方 API 凭据已脱敏

## 当前已经补齐的核心功能

- 行车日志的收藏 / 取消收藏
- 行车日志的评论反馈与管理员回复
- 基于用户偏好的推荐接口 `autoSort2`
- 多源车型知识采集与知识库页面
- 用户相关半成品接口修复
- Docker 化数据库初始化

## 目录说明

- `main/`：Django 业务代码
- `templates/front/admin/`：Vue 3 管理端
- `db/`：数据库初始化 SQL
- `docs/plans/`：本次补齐的设计与实施计划

## 爬虫说明

当前项目中的“爬虫”不再是旧模板里的空接口，而是一个真实可用的 **车型知识采集功能**：

- 采集对象：`vehiclemodel` 对应的公开车型知识
- 数据来源：优先抓取百度百科车型词条页，受反爬限制时自动退回公开搜索结果页；如果外部结果过少，会使用内置答辩演示知识库兜底，避免换电脑或遇到验证码时整页失败
- 入库位置：`vehicleknowledge` 表
- 前端入口：
  - `行车日志` 列表里的 `采集车型知识`
  - `车型知识库` 页里的 `批量采集` / `重新采集`

说明：

- 这个爬虫用于补全公开车型资料，不用于伪造原始行车遥测日志。
- 行车日志主数据仍然以数据库已有数据和 Excel 导入为主。
- 答辩前可执行 `python manage.py prepare_demo_data` 清理旧的失败采集记录并标准化演示车型，也可以直接双击 `准备答辩数据.bat`。

## 推荐启动方式

### 1. 准备环境变量

首次运行先在项目根目录执行：

```bash
copy .env.example .env
```

如果你需要邮件找回密码，再按需补充这些环境变量：

- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `EMAIL_USE_SSL`
- `EMAIL_USE_TLS`

### 2. 启动 Docker 依赖服务

先启动 MySQL 和 Redis：

```bash
docker compose up -d db redis
```

首次空库启动时，MySQL 容器会自动执行这些初始化脚本：

- `db/diandong5k56la1f.sql`
- `db/init/002_feature_patch.sql`
- `db/init/003_demo_data_cleanup.sql`
- `db/init/004_prediction_upgrade.sql`

如果你本机已经存在旧的 MySQL 数据卷，或者是在这个仓库补功能之后才拉到最新代码，建议紧接着执行一次：

```bash
python manage.py sync_feature_schema
```

也可以直接双击仓库根目录下的 `升级数据库.bat`。

数据库默认使用：

- `DB_HOST=127.0.0.1`
- `DB_PORT=3306`
- `DB_NAME=diandong5k56la1f`
- `DB_USER=root`
- `DB_PASSWORD=123456`

Redis 默认使用：

- `REDIS_HOST=127.0.0.1`
- `REDIS_PORT=6379`
- `REDIS_PASSWORD=123456`
- `REDIS_DB=1`

### 3. 安装后端依赖

```bash
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate --fake-initial
python manage.py sync_feature_schema
```

说明：

- Django 会优先读取环境变量中的数据库配置，不够时再回退到 `config.ini`
- Django 现在会优先读取 `.env`，因此更推荐通过 `.env` 管理 Docker 连接参数
- Django 会优先使用 Redis 作为缓存和 session 后端；如果 Redis 未配置，会自动回退到本地内存缓存
- `manage.py` 现在默认不会自动打开浏览器
- `sync_feature_schema` 会把旧库缺失的收藏、评论、车型知识等表结构补齐，适合已经存在的 Docker 数据卷

### 4. 启动后端

```bash
python manage.py runserver --insecure 0.0.0.0:8080 --noreload
```

如果你明确想让它启动时自动打开后台页面，再手动设置：

```bash
set OPEN_ADMIN_ON_RUNSERVER=1
python manage.py runserver --insecure 0.0.0.0:8080 --noreload
```

### 5. 启动前端开发环境

```bash
cd templates/front/admin
npm install
npm run serve
```

### 6. 前端打包

```bash
cd templates/front/admin
npm run build
```

## 验证命令

这几条已经在当前机器上跑通过：

```bash
docker compose config
.\.venv\Scripts\python.exe -m unittest util.tests_configread -v
cd templates/front/admin && npm run build
```

## 说明

- 旧的批处理脚本仍然保留，但建议优先按上面的 Docker 流程使用
- 如果你需要彻底重建容器数据，可以执行 `docker compose down -v` 后再重新 `docker compose up -d db redis`
- 如果后面还要继续收口，最值得做的是人工走查一遍前端页面交互和权限细节
