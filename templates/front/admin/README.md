# 前端与本地联调说明

这个前端项目基于 `Vue 3 + Vite + Element Plus`，后端为 Django，数据库推荐固定走 Docker 里的 MySQL，方便整套项目迁移到另一台电脑时少踩环境坑。

## 环境要求

| 依赖 | 建议版本 | 说明 |
| --- | --- | --- |
| Node.js | `>= 22` | 前端构建与开发 |
| npm | `>= 10` | 包管理 |
| Python | `3.11` 附近 | Django 后端 |
| Docker Desktop | 最新稳定版 | 运行 MySQL 容器 |

## 1. 启动数据库

在项目根目录执行：

```bash
copy .env.example .env
docker compose up -d db
```

默认数据库配置如下：

- `DB_HOST=127.0.0.1`
- `DB_PORT=3306`
- `DB_NAME=diandong5k56la1f`
- `DB_USER=root`
- `DB_PASSWORD=123456`

说明：

- Django 现在会优先读取环境变量中的数据库配置，缺失时才回退到 `config.ini`。
- 数据库数据保存在 Docker 命名卷 `mysql_data` 中，不依赖某台电脑的固定目录。

## 2. 启动 Django 后端

仍然在项目根目录执行：

```bash
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py runserver --insecure 0.0.0.0:8080 --noreload
```

补充说明：

- `manage.py` 已改成默认不会自动打开浏览器。
- 如果你确实想在 `runserver` 时自动打开后台页面，可以先设置环境变量：

```bash
set OPEN_ADMIN_ON_RUNSERVER=1
python manage.py runserver --insecure 0.0.0.0:8080 --noreload
```

## 3. 启动前端

在 `templates/front/admin` 目录执行：

```bash
npm install
npm run serve
```

开发环境启动后，按 Vite 控制台输出的地址访问即可。

## 4. 前端打包

在 `templates/front/admin` 目录执行：

```bash
npm run build
```

本次功能补齐后的验证命令已经通过：

- `npm run build`
- `docker compose config`
- `python manage.py test -v 2 --noinput`

## 5. 本次补齐的前端功能

- `行车日志` 列表已接入 `评论`
- `行车日志` 列表已接入 `收藏/取消`
- `行车日志` 列表已接入 `采集车型知识`
- `行车日志` 页头已接入 `偏好推荐`
- 新增 `我的收藏` 页面配置
- 新增 `评论反馈` 页面配置
- 新增 `车型知识库` 页面配置

## 6. 车型知识采集说明

本次新增的爬虫功能用于采集公开车型知识，而不是直接生成行车日志。

- 采集入口一：`行车日志` 列表里的 `采集车型知识`
- 采集入口二：`车型知识库` 页里的 `批量采集` / `重新采集`
- 采集结果字段：车型名称、厂商/品牌、电池类型、官方续航、充电信息、车型简介、来源地址、采集状态
- 数据源策略：优先抓取百度百科车型词条页；遇到反爬或字段过少时，会退回公开搜索结果和内置答辩演示知识库兜底
- 答辩前建议在项目根目录执行 `python manage.py prepare_demo_data`，或双击 `准备答辩数据.bat`，再进入 `车型知识库` 点击 `批量采集`

## 7. 推荐使用的 VS Code 插件

```json
{
  "recommendations": [
    "Vue.volar",
    "esbenp.prettier-vscode"
  ]
}
```
