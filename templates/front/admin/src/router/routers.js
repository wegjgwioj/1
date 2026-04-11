/**
 * @description: 路由页面列表
 */

const ListPage = () => import("@/views/list/list.vue");

const routes = [
  {
    path: '/',
    component: () => import('@/views/layout/layout.vue'),
    redirect: '/login',
    children: [
      {
        path: '/home',
        component: () => import('@/views/home/home.vue'),
        meta: {
          title: '首页'
        },        
      },
      {
        path: '/center',
        component: () => import('@/views/center.vue'),
        meta: {
          title: '个人信息'
        },
      },
      {
        path: '/updatePassword',
        component: () => import('@/views/updatePassword.vue'),
        meta: {
          title: '修改密码',
        },
      },
      {
        path: '/config/:type',
        component: ListPage,
      },
      {
        path: '/user',
        component: ListPage,
        meta: {
          title: "用户",
        },        
      },  
      {
        path: '/drivinglog',
        component: ListPage,
        meta: {
          title: "行车日志",
        },        
      },
      {
        path: '/vehicleknowledge',
        component: ListPage,
        meta: {
          title: "车型知识库",
        },
      },
      {
        path: '/storeup',
        component: ListPage,
        meta: {
          title: "我的收藏",
        },
      },
      {
        path: '/discussdrivinglog',
        component: ListPage,
        meta: {
          title: "评论反馈",
        },
      },
      {
        path: '/drivinglogforecast',
        component: ListPage,
        meta: {
          title: "电池寿命预测",
        },        
      },  
      {
        path: '/users',
        component: ListPage,
        meta: {
          title: "管理员",
        },        
      },  
    ],
  },
  {
    path: '/login',
    component: () => import('@/views/login/login.vue'),
    meta: {
      title: "登录",
    },
  },
  {
    path: '/register',
    component: () => import('@/views/register/register.vue'),
    meta: {
      title: "注册",
    },
  },
  {
    path: '/forgetPassword',
    component: () => import('@/views/forgetPassword.vue'),
    meta: {
      title: '忘记密码',
    },
  },
  {
    path: '/board',
    component: () => import("@/views/board/index.vue"),
    meta: {
      title: "看板",
    },
  },  
]


export default routes
