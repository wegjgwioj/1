/**
 * @description 通用守卫配置
 * 1. 在路由守卫中使用 nprogress 来显示进度条
 */

import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

const PUBLIC_PATHS = new Set(['/login', '/register', '/forgetPassword'])
const BASIC_AUTH_PATHS = new Set(['/home', '/center', '/updatePassword'])

function getRoleMenu() {
  let roleMenu = localStorage.getItem('roleMenu')
  if (!roleMenu) {
    return []
  }

  try {
    return JSON.parse(roleMenu)
  } catch (error) {
    return []
  }
}

function findMenuByTableName(roleMenu, tableName) {
  for (const item of roleMenu) {
    if (item.tableName === tableName) {
      return item
    }

    if (item.child?.length) {
      const target = findMenuByTableName(item.child, tableName)
      if (target) {
        return target
      }
    }
  }

  return null
}

function canAccessPath(path) {
  if (PUBLIC_PATHS.has(path) || BASIC_AUTH_PATHS.has(path)) {
    return true
  }

  if (path.startsWith('/config/')) {
    return true
  }

  const roleMenu = getRoleMenu()
  if (!roleMenu.length) {
    return false
  }

  if (path === '/board') {
    return !!findMenuByTableName(roleMenu, 'hasBoard')?.buttons?.includes('查看')
  }

  const tableName = path.replace(/^\//, '')
  return !!findMenuByTableName(roleMenu, tableName)
}

function getHomePath() {
  const roleMenu = getRoleMenu()
  const hasBoard = findMenuByTableName(roleMenu, 'hasBoard')?.buttons?.includes('查看')
  return hasBoard ? '/board' : '/home'
}

function setupCommonGuard(router) {
  router.beforeEach((to, from, next) => {
    // 页面加载进度条
    NProgress.start()

    // 重定向到密码找回
    if (to.path === '/register' && to.query.pageFlag == 'security1') {
      next({
        path: '/forgetPassword',
        query: to.query,
      })
      return
    }

    const hasToken = !!localStorage.getItem('Token')
    const isPublicPage = PUBLIC_PATHS.has(to.path)

    if (!isPublicPage && !hasToken) {
      next({
        path: '/login',
        query: {
          redirect: to.fullPath,
        },
      })
      return
    }

    if (to.path === '/login' && hasToken) {
      next(to.query.redirect || getHomePath())
      return
    }

    if (!isPublicPage && !canAccessPath(to.path)) {
      ElMessage.warning('当前账号无权访问该页面，已为你返回首页')
      next(getHomePath())
      return
    }

    next()
  })

  router.afterEach(to => {
    NProgress.done()
  })
}

export default setupCommonGuard
