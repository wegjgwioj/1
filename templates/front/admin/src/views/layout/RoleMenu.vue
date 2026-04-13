
<script setup>
/**
 * @description 角色菜单
 */
import { inject } from 'vue'
const { roleMenus, userName, userAvatar, roleMenuEvent, notreadnum } = inject('header')
</script>

<template>
  <el-dropdown class="rolemenus" trigger="click" @command="roleMenuEvent">
    <div class="avatar">
      <span v-if="notreadnum" class="notreadnum">{{ notreadnum }}</span>
      <img class="img" :src="userAvatar" />
      <span class="name">{{ userName }}</span>
    </div>

    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item v-for="item in roleMenus" :key="item.key" :command="item.key">
          <div class="menu-item" :list-key="item.key">
            <el-icon>
              <component :is="item.icon" />
            </el-icon>
            <span>{{ item.label }}</span>
          </div>
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<style>
.rolemenus {
  color: inherit;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  .notreadnum {
    position: absolute;
    z-index: 9;
    left: 0;
    top: 0;
    background-color: #f56c6c;
    color: #fff;
    padding: 3px 6px;
    border-radius: 10px;
    font-size: 12px;
  }
  .avatar {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 10px;
    padding: 8px 10px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.85);
    border: 1px solid var(--sys-border);
    box-shadow: var(--sys-shadow-sm);
  }

  .img {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    border: 1px solid transparent;
  }

  .name {
    display: inline;
    font-size: 14px;
    font-weight: 600;
    color: var(--sys-text);
  }
}
</style>
  
