/**
 * @description: 对表格组件进一步封装、并全局注册
 */

const modules = import.meta.glob('./components/**/*.vue', { eager: true })

export function registerTableItemComponents(app) {
  for (const path in modules) {
    let fileName = path.split('/').pop().replace('.vue', '')
    app.component(fileName, modules[path].default)
  }
}
