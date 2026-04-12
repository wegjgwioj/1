import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile, access } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { constants } from 'node:fs'

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../../..')

async function readProjectFile(relativePath) {
  return readFile(path.join(projectRoot, relativePath), 'utf-8')
}

test('frontend entry does not load external codegen CDN scripts', async () => {
  const html = await readProjectFile('templates/front/admin/index.html')
  assert.doesNotMatch(html, /codegen\.caihongy\.cn/i)
  assert.doesNotMatch(html, /<script[^>]+https?:\/\//i)
})

test('frontend bootstrap does not dynamically inject remote UI scripts', async () => {
  const mainJs = await readProjectFile('templates/front/admin/src/main.js')
  assert.doesNotMatch(mainJs, /codegen\.caihongy\.cn/i)
  assert.doesNotMatch(mainJs, /window\.ElementPlus/i)
  assert.doesNotMatch(mainJs, /window\.ElementPlusIconsVue/i)
})

test('project source does not keep hard coded DeepSeek credentials', async () => {
  const editor = await readProjectFile(
    'templates/front/admin/src/components/FormItem/components/YyAiEditor.vue',
  )
  assert.doesNotMatch(editor, /sk-[A-Za-z0-9]{20,}/)
  assert.doesNotMatch(editor, /https:\/\/api\.deepseek\.com/i)
})

test('project source does not expose payment or hard coded mail secrets', async () => {
  const settingsPy = await readProjectFile('dj2/settings.py')
  const commonJs = await readProjectFile('templates/front/admin/src/api/common.js')

  assert.doesNotMatch(settingsPy, /ALIPAY_APP_ID|ALIPAY_PUBLIC_KEY_STRING|APP_PRIVATE_KEY_STRING/)
  assert.doesNotMatch(settingsPy, /EMAIL_HOST_USER\s*=\s*['"][^'"]+['"]/)
  assert.doesNotMatch(settingsPy, /EMAIL_HOST_PASSWORD\s*=\s*['"][^'"]+['"]/)
  assert.doesNotMatch(commonJs, /alipayAPI|\$\{tableName\}\/alipay/)
})

test('alipay key files are removed from the repository', async () => {
  const appPrivateKeyPath = path.join(projectRoot, 'util/alipay_key/app_private_2048.txt')
  const alipayPublicKeyPath = path.join(projectRoot, 'util/alipay_key/alipay_public_2048.txt')

  await assert.rejects(() => access(appPrivateKeyPath, constants.F_OK))
  await assert.rejects(() => access(alipayPublicKeyPath, constants.F_OK))
})

test('sql seed data does not contain third party API secrets', async () => {
  const sql = await readProjectFile('db/diandong5k56la1f.sql')
  assert.doesNotMatch(sql, /\\"appId\\":\\"\d{6,}\\"/)
  assert.doesNotMatch(sql, /\\"apiKey\\":\\"[^"]{8,}\\"/)
  assert.doesNotMatch(sql, /\\"secretKey\\":\\"[^"]{8,}\\"/)
})
