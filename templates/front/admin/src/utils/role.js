/**
 * @description 登录、注册模块的角色信息列表
 */
export let roleList = [
  {
    hasBackLogin: "是",
    hasBackRegister: "否",
    hasFrontLogin: "否",
    hasFrontRegister: "否",
    roleName: "管理员",
    tableName: "users",
    faceMatch: '否',
    passwordProtected: '否',
    emailRegister: '否',
    accountName: 'username',
    avatarName: 'image',
    examName: 'username',    
  }, 
  {
    hasBackLogin: '是',
    hasBackRegister: '是',
    hasFrontLogin: '是',
    hasFrontRegister: '是',
    tableName: 'user',
    roleName: '用户',
    faceMatch: '否',
    passwordProtected: '否',
    emailRegister: '否',
    accountName: 'useraccount',
    avatarName: 'headportrait',
    examName: 'useraccount', 
  },
]
