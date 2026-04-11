# 车型知识采集功能实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标：** 在项目内实现真实可用的车型知识爬虫，支持按车型采集、按日志触发采集、批量采集与结果展示。

**架构：** 继续沿用现有 Django + Vue 配置驱动结构，不引入独立 Scrapy 子工程。后端通过 `requests + lxml` 从百度百科抓取车型简介与基础信息，写入新增的 `vehicleknowledge` 表；前端新增车型知识库页面，并在行车日志页提供采集入口。

**技术栈：** Django、Vue 3、MySQL、requests、lxml、现有自动注册路由机制、Docker Compose。

---

### 任务 1：补设计对应的数据库结构

**文件：**
- 修改：`main/models.py`
- 修改：`db/init/002_feature_patch.sql`
- 测试：`main/tests.py`

**步骤 1：先写失败测试**

在 `main/tests.py` 中新增模型冒烟测试，断言 `vehicleknowledge` 模型存在，且拥有 `vehiclemodel`、`summary`、`crawlstatus` 等关键字段。

**步骤 2：运行测试，确认它按预期失败**

运行：

```bash
python manage.py test main.tests.ModelSmokeTest -v 2
```

预期：因 `vehicleknowledge` 不存在而失败。

**步骤 3：编写最小实现**

1. 在 `main/models.py` 中新增 `vehicleknowledge`
2. 在 `db/init/002_feature_patch.sql` 中补充建表 SQL

**步骤 4：再次运行测试，确认通过**

运行：

```bash
python manage.py test main.tests.ModelSmokeTest -v 2
```

预期：PASS。

### 任务 2：先补采集解析测试

**文件：**
- 新建：`util/vehicle_knowledge_crawler.py`
- 测试：`main/tests.py`

**步骤 1：先写失败测试**

新增解析测试，使用本地 HTML 片段断言：

1. 能提取车型简介
2. 能提取厂商字段
3. 能提取续航与电池类型

**步骤 2：运行测试，确认它按预期失败**

运行：

```bash
python manage.py test main.tests.VehicleKnowledgeParserTest -v 2
```

预期：因解析函数不存在或返回空值而失败。

**步骤 3：编写最小实现**

在 `util/vehicle_knowledge_crawler.py` 中实现：

1. 简介提取
2. 基础信息提取
3. 关键字段映射

**步骤 4：再次运行测试，确认通过**

运行：

```bash
python manage.py test main.tests.VehicleKnowledgeParserTest -v 2
```

预期：PASS。

### 任务 3：实现车型知识视图与采集接口

**文件：**
- 新建：`main/Vehicleknowledge_v.py`
- 修改：`main/urls.py`
- 测试：`main/tests.py`

**步骤 1：先写失败测试**

新增接口测试：

1. `crawlByModel` 在 mock 成功响应时写入数据库
2. 重复采集同一车型时执行更新而非重复插入
3. `crawlBatch` 能按 `drivinglog` 中车型去重采集

**步骤 2：运行测试，确认它按预期失败**

运行：

```bash
python manage.py test main.tests.VehicleKnowledgeCrawlFlowTest -v 2
```

预期：接口不存在或返回错误而失败。

**步骤 3：编写最小实现**

1. 实现 `vehicleknowledge` 常规 CRUD 视图
2. 实现 `crawlByModel`
3. 实现 `crawlBatch`
4. 实现 `queryByModel`

**步骤 4：再次运行测试，确认通过**

运行：

```bash
python manage.py test main.tests.VehicleKnowledgeCrawlFlowTest -v 2
```

预期：PASS。

### 任务 4：接入前端车型知识库页面

**文件：**
- 新建：`templates/front/admin/src/config/vehicleknowledge/table.js`
- 修改：`templates/front/admin/src/router/routers.js`
- 修改：`templates/front/admin/src/utils/menu.js`
- 修改：`templates/front/admin/src/api/list.js`
- 修改：`templates/front/admin/src/views/list/list.vue`

**步骤 1：先写失败验证**

本任务以前端构建验证为主，不单独写前端单测。

**步骤 2：编写最小实现**

1. 新增 `车型知识库` 路由和菜单
2. 新增采集 API 封装
3. 在通用列表页支持“批量采集”“重新采集”“行车日志采集车型知识”动作

**步骤 3：运行验证**

运行：

```bash
cd templates/front/admin
npm run build
```

预期：构建通过。

### 任务 5：做整体验证

**文件：**
- 修改：`README.md`
- 修改：`templates/front/admin/README.md`
- 测试：`main/tests.py`

**步骤 1：补文档**

更新 README，说明车型知识采集的用途和入口。

**步骤 2：运行后端验证**

运行：

```bash
python manage.py test -v 2 --noinput
```

预期：所有测试通过。

**步骤 3：运行前端验证**

运行：

```bash
cd templates/front/admin
npm run build
```

预期：构建通过。

**步骤 4：运行容器配置验证**

运行：

```bash
docker compose config
```

预期：配置解析成功。
