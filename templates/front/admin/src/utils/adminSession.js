export const ADMIN_SESSION_KEYS = [
  'Token',
  'sessionTable',
  'username',
  'userForm',
  'userid',
  'useravatar',
  'menus',
  'roleMenu',
  'role',
]

function removeScopedKeys(storage) {
  if (!storage || typeof storage.removeItem !== 'function') {
    return
  }

  ADMIN_SESSION_KEYS.forEach((key) => {
    storage.removeItem(key)
  })
}

export function clearAdminSession(localStorageRef = globalThis.localStorage, sessionStorageRef = null) {
  removeScopedKeys(localStorageRef)
  removeScopedKeys(sessionStorageRef)
}
