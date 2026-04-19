import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile, readdir } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import {
  headerButtons as drivinglogHeaderButtons,
  tableButtons as drivinglogTableButtons,
} from '../src/config/drivinglog/table.js'
import {
  columns as discussColumns,
  headerButtons as discussHeaderButtons,
  tableButtons as discussTableButtons,
} from '../src/config/discussdrivinglog/table.js'
import { getAuthButtons } from '../src/utils/auth.js'
import { initMenus } from '../src/utils/menu.js'

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../../..')

function visibleButtonTitles(buttons, authButtonNames) {
  return buttons
    .filter(button => button.isPublic || authButtonNames.includes(button.name))
    .map(button => button.title)
}

function findButton(buttons, title) {
  return buttons.find(button => button.title === title)
}

function installLocalStorage() {
  const store = new Map()
  global.localStorage = {
    getItem(key) {
      return store.has(key) ? store.get(key) : null
    },
    setItem(key, value) {
      store.set(key, String(value))
    },
    removeItem(key) {
      store.delete(key)
    },
    clear() {
      store.clear()
    },
  }
}

test('user role drivinglog actions exclude admin maintenance buttons', () => {
  const userDrivinglogAuthButtons = ['查看', '偏好推荐', '评论', '收藏/取消']

  assert.deepEqual(visibleButtonTitles(drivinglogHeaderButtons, userDrivinglogAuthButtons), [
    '偏好推荐',
  ])
  assert.deepEqual(visibleButtonTitles(drivinglogTableButtons, userDrivinglogAuthButtons), [
    '评论',
    '收藏/取消',
    '查看',
  ])
})

test('drivinglog maintenance buttons require explicit non-public permissions', () => {
  const dataClean = findButton(drivinglogHeaderButtons, '数据清洗')
  const crawlVehicleKnowledge = findButton(drivinglogTableButtons, '采集车型知识')

  assert.equal(dataClean?.isPublic, undefined)
  assert.equal(dataClean?.name, '数据清洗')
  assert.equal(crawlVehicleKnowledge?.isPublic, undefined)
  assert.equal(crawlVehicleKnowledge?.name, '采集车型知识')
})

test('vehicle knowledge crawl actions show immediate loading feedback', async () => {
  const listView = await readFile(
    path.join(projectRoot, 'templates/front/admin/src/views/list/list.vue'),
    'utf-8',
  )

  assert.match(listView, /车型知识采集中，请稍候/)
  assert.match(listView, /批量采集中，请稍候/)
})

test('discuss permissions follow role menu instead of granting all discuss actions', async () => {
  installLocalStorage()
  await initMenus()
  const menus = JSON.parse(localStorage.getItem('menus'))

  const userRole = menus.find(item => item.tableName === 'user')
  localStorage.setItem('roleMenu', JSON.stringify(userRole.backMenu))
  assert.deepEqual(getAuthButtons('discussdrivinglog'), ['查看'])
  assert.deepEqual(visibleButtonTitles(discussHeaderButtons, getAuthButtons('discussdrivinglog')), [])
  assert.deepEqual(visibleButtonTitles(discussTableButtons, getAuthButtons('discussdrivinglog')), [
    '查看',
  ])

  const adminRole = menus.find(item => item.tableName === 'users')
  localStorage.setItem('roleMenu', JSON.stringify(adminRole.backMenu))
  assert.deepEqual(getAuthButtons('discussdrivinglog'), ['查看', '删除', '修改'])
  assert.deepEqual(visibleButtonTitles(discussHeaderButtons, getAuthButtons('discussdrivinglog')), [
    '删除',
  ])
  assert.deepEqual(visibleButtonTitles(discussTableButtons, getAuthButtons('discussdrivinglog')), [
    '查看',
    '回复',
    '删除',
  ])
})

test('menu initialization refreshes stale role permissions for current user session', async () => {
  installLocalStorage()
  localStorage.setItem('sessionTable', 'user')
  localStorage.setItem(
    'roleMenu',
    JSON.stringify([
      {
        menu: '互动管理',
        child: [
          {
            menu: '评论反馈',
            tableName: 'discussdrivinglog',
            buttons: ['新增', '查看', '删除'],
          },
        ],
      },
    ]),
  )

  await initMenus()

  assert.deepEqual(getAuthButtons('discussdrivinglog'), ['查看'])
})

test('discuss comment content uses a registered textarea component', async () => {
  const componentDir = path.join(
    projectRoot,
    'templates/front/admin/src/components/FormItem/components',
  )
  const registeredComponentNames = (await readdir(componentDir))
    .filter(fileName => fileName.endsWith('.vue'))
    .map(fileName => fileName.replace(/\.vue$/, ''))

  const contentColumn = discussColumns.find(column => column.columnName === 'content')
  assert.equal(contentColumn?.form_hidden, false)
  assert.equal(contentColumn?.form_type, 'YyTextArea')
  assert.ok(registeredComponentNames.includes(contentColumn.form_type))
})

test('discuss list shows vehicle association and display-only reply status', () => {
  const visibleColumnNames = discussColumns
    .filter(column => !column.hiden || !column.hiden.includes('2'))
    .map(column => column.columnName)
  const viewColumnNames = discussColumns
    .filter(column => !column.hiden || !column.hiden.includes('3'))
    .map(column => column.columnName)
  const rawReplyColumn = discussColumns.find(column => column.columnName === 'reply')
  const replyDisplayColumn = discussColumns.find(column => column.columnName === 'replydisplay')

  assert.ok(visibleColumnNames.includes('vehicleinfo'))
  assert.ok(visibleColumnNames.includes('replydisplay'))
  assert.ok(viewColumnNames.includes('replydisplay'))
  assert.equal(replyDisplayColumn?.comments, '回复记录')
  assert.match(rawReplyColumn?.hiden || '', /2/)
  assert.match(rawReplyColumn?.hiden || '', /3/)
})
