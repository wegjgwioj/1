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
