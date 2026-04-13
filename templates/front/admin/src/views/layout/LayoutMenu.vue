<script setup>
/**
 * @description 垂直菜单 说明
 * 必填:
 * @param { Array } menus 菜单列表
 * @param { Function } clickEvent 点击跳转页面方法
 *
 * 选填:
 * @param { Boolean } isCollapse 是否折叠
 * @param { Function } switchCollapse 折叠/展开
 */
import { ref, watch, inject } from 'vue'
import { useRoute } from 'vue-router'
const { menus, isCollapse, switchCollapse, clickEvent } = inject('header')

// 激活的菜单项,默认首页
const route = useRoute()
const defaultActive = ref('/home')
watch(
  () => route.path,
  newPath => {
    defaultActive.value = newPath
  },
  { immediate: true }
)
</script>

<template>
  <!-- 菜单 -->
  <aside>
    <div class="menu-brand">
      <div class="menu-brand-mark">EV</div>
      <div class="menu-brand-title">运行监测与预测平台</div>
      <div class="menu-brand-subtitle">日志采集、知识补全、风险评估与模型分析</div>
    </div>
    <el-scrollbar>
      <el-menu
        popper-class="menu-poper"
        :default-active="defaultActive"
        :collapse="isCollapse"
        unique-opened
      >
        <!-- 首页 -->
        <el-menu-item index="/home" @click="clickEvent('/home')">
          <el-icon>
            <HomeFilled />
          </el-icon>
          <span>首页</span>
        </el-menu-item>

        <!-- 个人中心 -->
        <el-sub-menu index="/center">
          <template #title>
            <el-icon>
              <UserFilled />
            </el-icon>
            <span>个人中心</span>
          </template>

          <el-menu-item index="/center" @click="clickEvent('/center')">
            <span>个人信息</span>
          </el-menu-item>

          <el-menu-item index="/updatePassword" @click="clickEvent('/updatePassword')">
            <span>修改密码</span>
          </el-menu-item>
        </el-sub-menu>

        <!-- 其它菜单 -->
        <template v-for="(item, index) in menus">
          <!-- child大于2个以上的话，二级菜单,像个人中心那样 -->
          <el-sub-menu v-if="item.child.length > 1" :index="item.menu">
            <template #title>
              <el-icon>
                <component :is="item.icon" />
              </el-icon>
              <span>{{ item.menu }}</span>
            </template>

            <el-menu-item
              v-for="i in item.child"
              :index="'/' + i.tableName"
              @click="clickEvent('/' + i.tableName)"
            >
              <span>{{ i.menu }}</span>
            </el-menu-item>
          </el-sub-menu>

          <!-- child只有1个,一级菜单，像首页那样 -->
          <el-menu-item
            v-if="item.child.length == 1"
            :index="'/' + item.child[0].tableName"
            @click="clickEvent('/' + item.child[0].tableName)"
          >
            <el-icon>
              <component :is="item.icon" />
            </el-icon>
            <span>{{ item.child[0].menu }}</span>
          </el-menu-item>
        </template>
      </el-menu>
    </el-scrollbar>

    <!-- 折叠按钮 -->

  </aside>
</template>

<style>
.menu-wrapper {
  .el-menu {
    border-right: none;
    overflow: hidden;
  }
}
</style>
