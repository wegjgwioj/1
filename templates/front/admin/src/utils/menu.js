/**
 * @description 菜单
 * 每次初始化,更新菜单到localStorage,其它功能默认从localStorage读取
 */

export async function initMenus() {
  let menus = roleMenus
  localStorage.setItem('menus', JSON.stringify(menus))

  const sessionTable = localStorage.getItem('sessionTable')
  if (sessionTable) {
    const currentRole = roleMenus.find(item => item.tableName === sessionTable)
    if (currentRole) {
      localStorage.setItem('roleMenu', JSON.stringify(currentRole.backMenu))
      localStorage.setItem('role', currentRole.roleName)
    }
  }
}

const roleMenus = [
  {
    backMenu: [
      {
        menu: '运行日志',
        child: [
          {
            allButtons: ['新增', '查看', '修改', '删除', '偏好推荐', '评论', '收藏/取消', '电池容量分析', '电池寿命', '路线分布', '驾驶评分', '节能建议', '导出', '导入', '上传模板', '下载模板', '首页总数', '首页统计'],
            appFrontIcon: 'cuIcon-pay',
            buttons: ['查看', '偏好推荐', '评论', '收藏/取消'],
            menu: '行车日志',
            menuJump: '列表',
            tableName: 'drivinglog',
          },
        ],
      },
      {
        menu: '车型知识',
        child: [
          {
            allButtons: ['查看', '重新采集', '批量采集'],
            appFrontIcon: 'cuIcon-news',
            buttons: ['查看', '重新采集', '批量采集'],
            menu: '车型知识库',
            menuJump: '列表',
            tableName: 'vehicleknowledge',
          },
        ],
      },
      {
        menu: '互动管理',
        child: [
          {
            allButtons: ['查看', '删除'],
            appFrontIcon: 'cuIcon-favor',
            buttons: ['查看', '删除'],
            menu: '我的收藏',
            menuJump: '列表',
            tableName: 'storeup',
          },
          {
            allButtons: ['查看'],
            appFrontIcon: 'cuIcon-message',
            buttons: ['查看'],
            menu: '评论反馈',
            menuJump: '列表',
            tableName: 'discussdrivinglog',
          },
        ],
      },
      {
        menu: '预测分析',
        child: [
          {
            allButtons: ['新增', '查看', '预测', '预测工作台'],
            appFrontIcon: 'cuIcon-album',
            buttons: ['新增', '查看', '预测', '预测工作台'],
            menu: '预测记录',
            menuJump: '列表',
            tableName: 'drivinglogforecast',
          },
          {
            allButtons: ['查看'],
            appFrontIcon: 'cuIcon-album',
            buttons: ['查看'],
            menu: '预测工作台',
            menuJump: '工作台',
            tableName: 'forecastWorkbench',
          },
        ],
      },
      {
        menu: '看板管理',
        child: [
          {
            allButtons: ['查看'],
            appFrontIcon: 'cuIcon-flashlightopen',
            buttons: ['查看'],
            menu: '看板',
            tableName: 'hasBoard',
          },
        ],
      },
    ],
    frontMenu: [],
    hasBackLogin: '是',
    hasBackRegister: '是',
    hasFrontLogin: '是',
    hasFrontRegister: '是',
    roleName: '用户',
    tableName: 'user',
  },
  {
    backMenu: [
      {
        menu: '用户管理',
        child: [
          {
            allButtons: ['新增', '查看', '修改', '删除'],
            appFrontIcon: 'cuIcon-link',
            buttons: ['新增', '查看', '修改', '删除'],
            menu: '用户',
            menuJump: '列表',
            tableName: 'user',
          },
        ],
      },
      {
        menu: '运行日志',
        child: [
          {
            allButtons: ['新增', '查看', '修改', '删除', '偏好推荐', '评论', '收藏/取消', '采集车型知识', '数据清洗', '电池容量分析', '电池寿命', '路线分布', '驾驶评分', '节能建议', '导出', '导入', '上传模板', '下载模板', '首页总数', '首页统计'],
            appFrontIcon: 'cuIcon-pay',
            buttons: ['新增', '查看', '修改', '删除', '偏好推荐', '评论', '收藏/取消', '采集车型知识', '数据清洗', '导出', '导入', '首页总数', '首页统计'],
            menu: '行车日志',
            menuJump: '列表',
            tableName: 'drivinglog',
          },
        ],
      },
      {
        menu: '车型知识',
        child: [
          {
            allButtons: ['新增', '查看', '修改', '删除', '重新采集', '批量采集'],
            appFrontIcon: 'cuIcon-news',
            buttons: ['新增', '查看', '修改', '删除', '重新采集', '批量采集'],
            menu: '车型知识库',
            menuJump: '列表',
            tableName: 'vehicleknowledge',
          },
        ],
      },
      {
        menu: '互动管理',
        child: [
          {
            allButtons: ['查看', '删除'],
            appFrontIcon: 'cuIcon-favor',
            buttons: ['查看', '删除'],
            menu: '我的收藏',
            menuJump: '列表',
            tableName: 'storeup',
          },
          {
            allButtons: ['查看', '删除', '修改'],
            appFrontIcon: 'cuIcon-message',
            buttons: ['查看', '删除', '修改'],
            menu: '评论反馈管理',
            menuJump: '列表',
            tableName: 'discussdrivinglog',
          },
        ],
      },
      {
        menu: '预测分析',
        child: [
          {
            allButtons: ['新增', '查看', '修改', '删除', '预测', '预测工作台'],
            appFrontIcon: 'cuIcon-album',
            buttons: ['新增', '查看', '修改', '删除', '预测', '预测工作台'],
            menu: '预测记录',
            menuJump: '列表',
            tableName: 'drivinglogforecast',
          },
          {
            allButtons: ['查看'],
            appFrontIcon: 'cuIcon-album',
            buttons: ['查看'],
            menu: '预测工作台',
            menuJump: '工作台',
            tableName: 'forecastWorkbench',
          },
        ],
      },
      {
        menu: '看板管理',
        child: [
          {
            allButtons: ['查看'],
            appFrontIcon: 'cuIcon-flashlightopen',
            buttons: ['查看'],
            menu: '看板',
            tableName: 'hasBoard',
          },
        ],
      },
    ],
    frontMenu: [],
    hasBackLogin: '是',
    hasBackRegister: '否',
    hasFrontLogin: '否',
    hasFrontRegister: '否',
    roleName: '管理员',
    tableName: 'users',
  },
]
