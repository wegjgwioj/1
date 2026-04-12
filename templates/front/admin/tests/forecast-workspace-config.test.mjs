import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

import routes from '../src/router/routers.js'
import * as forecastTableConfig from '../src/config/drivinglogforecast/table.js'

test('router exposes a dedicated forecast workspace page', () => {
  const rootRoute = routes.find((item) => item.path === '/')
  assert.ok(rootRoute)
  const workspaceRoute = rootRoute.children.find((item) => item.path === '/forecastWorkbench')
  assert.ok(workspaceRoute)
  assert.equal(workspaceRoute.meta.title, '预测工作台')
})

test('drivinglogforecast header buttons expose workspace entry', () => {
  const hasWorkspaceButton = forecastTableConfig.headerButtons.some(
    (item) => item.key === 'forecastWorkspace' && item.name === '预测工作台',
  )
  assert.equal(hasWorkspaceButton, true)
})

test('role menu config contains a direct forecast workspace menu item', async () => {
  const content = await readFile(new URL('../src/utils/menu.js', import.meta.url), 'utf-8')
  assert.match(content, /tableName:\s*'forecastWorkbench'/)
  assert.match(content, /menu:\s*'预测工作台'/)
})

test('forecast workspace view exposes ML and DL comparison summary fields', async () => {
  const content = await readFile(new URL('../src/views/board/Forecast.vue', import.meta.url), 'utf-8')
  assert.match(content, /同输入 ML \/ DL 结果对比/)
  assert.match(content, /DL 后端/)
  assert.match(content, /训练来源/)
  assert.match(content, /样本量/)
  assert.match(content, /DL 版本/)
})

test('forecast workspace view exposes NASA experiment section', async () => {
  const content = await readFile(new URL('../src/views/board/Forecast.vue', import.meta.url), 'utf-8')
  assert.match(content, /NASA 真实寿命实验/)
  assert.match(content, /SOH/)
  assert.match(content, /RUL/)
})

test('http utility clears local storage with the standard API on auth failures', async () => {
  const content = await readFile(new URL('../src/utils/http.js', import.meta.url), 'utf-8')
  assert.doesNotMatch(content, /localStorage\.removeItems\(/)
  assert.match(content, /localStorage\.clear\(\)/)
})
