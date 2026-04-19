import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../../..')

test('chart item skips async setOption after component unmount', async () => {
  const chartItem = await readFile(
    path.join(projectRoot, 'templates/front/admin/src/components/Echart/ChartItem.vue'),
    'utf-8',
  )

  assert.match(chartItem, /let isUnmounted = false/)
  assert.match(chartItem, /if \(!chartInstance \|\| isUnmounted\) \{\s*return\s*\}/)
})
