# 电动汽车行车日志系统

这个仓库现在的主线已经比较明确了：

- Django 后端负责业务接口、数据管理、推荐逻辑和预测接口
- Vue 3 后台前端负责列表页、收藏、评论反馈、推荐和车型知识采集入口
- MySQL 统一建议跑在 Docker 里，尽量减少换电脑后的环境问题

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

### 2. 启动 Docker 数据库

```bash
docker compose up -d db
```

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

### 3. 安装后端依赖

```bash
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate --fake-initial
python manage.py sync_feature_schema
```

说明：

- Django 会优先读取环境变量中的数据库配置，不够时再回退到 `config.ini`
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
.\.venv\Scripts\python.exe manage.py test -v 2 --noinput
cd templates/front/admin && npm run build
```

## 说明

- 旧的批处理脚本仍然保留，但建议优先按上面的 Docker 流程使用
- 如果后面还要继续收口，最值得做的是人工走查一遍前端页面交互和权限细节
