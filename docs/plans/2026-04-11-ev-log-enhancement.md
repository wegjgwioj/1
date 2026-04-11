# 电动汽车行车日志系统功能补齐实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标：** 补齐收藏、评论反馈、偏好推荐能力，并修复若干明显半成品问题，同时提供 Docker 化数据库方案，确保项目更容易迁移到另一台电脑运行。

**架构：** 继续沿用现有 Django + Vue 配置驱动结构，不重做整体架构。通过新增 `storeup`、`discussdrivinglog` 两张业务表、扩展 `drivinglog` 字段、补齐 `autoSort2` 逻辑和前端按钮配置，实现对论文与 `1.txt` 的代码侧对齐。

**技术栈：** Django、Vue 3、MySQL 8、Docker Compose、PyMySQL、现有模板自动路由机制。

---

### 任务 1：补齐数据库容器化方案

**文件：**
- 新建：`docker-compose.yml`
- 新建：`.env.example`
- 新建：`db/init/002_feature_patch.sql`
- 修改：`dj2/settings.py`
- 修改：`main/Drivinglogforecast_v.py`
- 修改：`util/configread.py`

**步骤 1：先写失败测试**

本任务以配置验证为主，不单独写自动化测试，后续通过命令验证。

**步骤 2：编写最小实现**

实现内容：

1. `docker-compose.yml` 中新增 `db` 服务，使用 `mysql:8.0`
2. 将 `db/diandong5k56la1f.sql` 和 `db/init/002_feature_patch.sql` 挂载到 `/docker-entrypoint-initdb.d/`
3. `.env.example` 中提供数据库连接变量
4. Django 与预测模块优先读环境变量，缺省时回退到 `config.ini`

**步骤 3：运行验证**

运行：

```bash
docker compose config
```

预期：配置解析成功，无语法错误。

**步骤 4：提交**

```bash
git add docker-compose.yml .env.example db/init/002_feature_patch.sql dj2/settings.py main/Drivinglogforecast_v.py util/configread.py
git commit -m "feat: add dockerized mysql configuration"
```

### 任务 2：扩展后端模型

**文件：**
- 修改：`main/models.py`

**步骤 1：先写失败测试**

在 `main/tests.py` 中新增模型字段存在性测试草稿，先断言 `storeup`、`discussdrivinglog` 可被导入，`drivinglog` 拥有 `storeupnum`、`discussnum`。

**步骤 2：运行测试，确认它按预期失败**

运行：

```bash
python manage.py test main.tests.ModelSmokeTest -v 2
```

预期：因模型不存在或字段不存在而失败。

**步骤 3：编写最小实现**

在 `main/models.py` 中：

1. 为 `drivinglog` 增加 `storeupnum`、`discussnum`
2. 新增 `storeup`
3. 新增 `discussdrivinglog`

**步骤 4：再次运行测试，确认通过**

运行：

```bash
python manage.py test main.tests.ModelSmokeTest -v 2
```

预期：PASS。

**步骤 5：提交**

```bash
git add main/models.py main/tests.py
git commit -m "feat: add storeup and discuss models"
```

### 任务 3：补齐收藏视图

**文件：**
- 新建：`main/Storeup_v.py`
- 修改：`main/urls.py`（仅在需要定制路由时）
- 测试：`main/tests.py`

**步骤 1：先写失败测试**

新增测试：

1. 首次收藏成功
2. 再次调用切换为取消收藏
3. `drivinglog.storeupnum` 随之变化

**步骤 2：运行测试，确认它按预期失败**

运行：

```bash
python manage.py test main.tests.StoreupFlowTest -v 2
```

预期：接口或表不存在导致失败。

**步骤 3：编写最小实现**

实现：

1. 标准增删改查接口
2. `toggle` 接口
3. `isStoreup` 接口
4. 收藏成功/取消时同步更新 `drivinglog.storeupnum`

**步骤 4：再次运行测试，确认通过**

运行：

```bash
python manage.py test main.tests.StoreupFlowTest -v 2
```

预期：PASS。

**步骤 5：提交**

```bash
git add main/Storeup_v.py main/tests.py
git commit -m "feat: add storeup flow"
```

### 任务 4：补齐评论反馈视图

**文件：**
- 新建：`main/Discussdrivinglog_v.py`
- 测试：`main/tests.py`

**步骤 1：先写失败测试**

新增测试：

1. 新增评论成功
2. 回复评论后 `reply` 字段写入 JSON
3. `drivinglog.discussnum` 同步增加

**步骤 2：运行测试，确认它按预期失败**

运行：

```bash
python manage.py test main.tests.DiscussFlowTest -v 2
```

预期：接口或表不存在导致失败。

**步骤 3：编写最小实现**

实现：

1. 标准评论增删改查
2. 评论新增时自动写入用户信息
3. 回复时兼容前端 `reply` JSON 结构
4. 同步更新 `drivinglog.discussnum`

**步骤 4：再次运行测试，确认通过**

运行：

```bash
python manage.py test main.tests.DiscussFlowTest -v 2
```

预期：PASS。

**步骤 5：提交**

```bash
git add main/Discussdrivinglog_v.py main/tests.py
git commit -m "feat: add discuss drivinglog flow"
```

### 任务 5：补齐推荐接口

**文件：**
- 修改：`main/Drivinglog_v.py`
- 测试：`main/tests.py`

**步骤 1：先写失败测试**

新增测试：

1. 有收藏偏好时，返回命中车型或路线的日志
2. 无偏好时，接口能返回默认列表

**步骤 2：运行测试，确认它按预期失败**

运行：

```bash
python manage.py test main.tests.RecommendationTest -v 2
```

预期：`autoSort2` 仍为空逻辑，断言失败。

**步骤 3：编写最小实现**

在 `main/Drivinglog_v.py` 中实现：

1. 收集用户收藏偏好
2. 收集用户最近浏览偏好
3. 计算推荐分值
4. 返回稳定排序结果
5. 无偏好时退化为最新列表

**步骤 4：再次运行测试，确认通过**

运行：

```bash
python manage.py test main.tests.RecommendationTest -v 2
```

预期：PASS。

**步骤 5：提交**

```bash
git add main/Drivinglog_v.py main/tests.py
git commit -m "feat: implement preference-based recommendation"
```

### 任务 6：修复用户相关半成品接口

**文件：**
- 修改：`main/Users_v.py`
- 修改：`main/User_v.py`
- 测试：`main/tests.py`

**步骤 1：先写失败测试**

新增测试：

1. `users_accountList` 可稳定返回账号列表
2. `user_importExcel` 与 `users_importExcel` 至少能够拒绝空数据并稳定返回

**步骤 2：运行测试，确认它按预期失败**

运行：

```bash
python manage.py test main.tests.UserUtilityTest -v 2
```

预期：出现未定义变量或空壳逻辑导致失败。

**步骤 3：编写最小实现**

实现：

1. 修复 `users_accountList`
2. 为 `user/users importExcel` 增加基础字段映射或最少稳定兜底
3. 为 `user/users autoSort2` 提供稳定默认列表

**步骤 4：再次运行测试，确认通过**

运行：

```bash
python manage.py test main.tests.UserUtilityTest -v 2
```

预期：PASS。

**步骤 5：提交**

```bash
git add main/Users_v.py main/User_v.py main/tests.py
git commit -m "fix: repair user utility endpoints"
```

### 任务 7：补齐前端评论与收藏入口

**文件：**
- 新建：`templates/front/admin/src/config/storeup/table.js`
- 新建：`templates/front/admin/src/config/discussdrivinglog/table.js`
- 修改：`templates/front/admin/src/config/drivinglog/table.js`
- 修改：`templates/front/admin/src/views/list/list.vue`
- 修改：`templates/front/admin/src/api/list.js`
- 修改：`templates/front/admin/src/utils/menu.js`

**步骤 1：先写失败验证**

本任务以前端手工验证为主，先记录验证目标：

1. 行车日志列表出现评论与收藏按钮
2. 能进入评论页
3. 能触发收藏/取消收藏
4. 菜单中能看到我的收藏

**步骤 2：编写最小实现**

实现：

1. `drivinglog` 开启评论能力
2. 增加收藏按钮定义
3. 新增 `storeup`、`discussdrivinglog` 配置
4. 在 `list.vue` 中补收藏事件与推荐事件接入
5. 在菜单中增加“我的收藏”“评论反馈管理”入口

**步骤 3：运行验证**

运行：

```bash
cd templates/front/admin
npm run build
```

预期：前端构建成功。

**步骤 4：提交**

```bash
git add templates/front/admin/src/config/storeup/table.js templates/front/admin/src/config/discussdrivinglog/table.js templates/front/admin/src/config/drivinglog/table.js templates/front/admin/src/views/list/list.vue templates/front/admin/src/api/list.js templates/front/admin/src/utils/menu.js
git commit -m "feat: wire frontend collect and discuss flows"
```

### 任务 8：全量验证

**文件：**
- 修改：`main/tests.py`
- 修改：`templates/front/admin/README.md`

**步骤 1：运行后端测试**

运行：

```bash
python manage.py test -v 2
```

预期：全部通过。

**步骤 2：运行前端构建**

运行：

```bash
cd templates/front/admin
npm run build
```

预期：构建成功。

**步骤 3：运行 Docker 配置校验**

运行：

```bash
docker compose config
```

预期：成功输出合成配置。

**步骤 4：补充说明文档**

在 `templates/front/admin/README.md` 或仓库说明中写清：

1. 如何复制 `.env`
2. 如何启动数据库容器
3. 如何启动 Django
4. 如何启动前端

**步骤 5：提交**

```bash
git add main/tests.py templates/front/admin/README.md
git commit -m "docs: add local setup and verification notes"
```
