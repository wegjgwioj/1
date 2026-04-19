import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../../..')

async function readProjectFile(relativePath) {
  return readFile(path.join(projectRoot, relativePath), 'utf-8')
}

test('component registries do not import the mounted app instance', async () => {
  const tableItemRegistry = await readProjectFile(
    'templates/front/admin/src/components/TableItem/index.js',
  )
  const formItemRegistry = await readProjectFile(
    'templates/front/admin/src/components/FormItem/index.js',
  )

  assert.doesNotMatch(tableItemRegistry, /import app from ['"]@\/main['"]/)
  assert.doesNotMatch(formItemRegistry, /import app from ['"]@\/main['"]/)
})

test('main bootstrap registers component registries before mounting the app', async () => {
  const mainSource = await readProjectFile('templates/front/admin/src/main.js')

  assert.match(mainSource, /registerTableItemComponents\(app\)/)
  assert.match(mainSource, /registerFormItemComponents\(app\)/)
  assert.match(mainSource, /app\.mount\('#app'\)/)
})
