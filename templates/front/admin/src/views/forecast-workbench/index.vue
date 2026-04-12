<script setup>
import '@/style/board.scss'

import { useRouter } from 'vue-router'

import Forecast from '@/views/board/Forecast.vue'

const router = useRouter()
</script>

<template>
  <div class="board forecast-workspace-page">
    <div class="header forecast-workspace-header">
      <div class="title">电池寿命预测工作台</div>
      <div class="time">
        <el-button type="primary" icon="List" text @click="router.push('/drivinglogforecast')">
          返回预测列表
        </el-button>
        <el-button type="primary" icon="HomeFilled" text @click="router.push('/home')">
          回首页
        </el-button>
      </div>
    </div>

    <div class="forecast-workspace-content">
      <Forecast />
    </div>
  </div>
</template>

<style scoped>
.forecast-workspace-page {
  min-height: 100%;
  padding-bottom: 20px;
}

.forecast-workspace-header {
  min-height: 88px;
}

.forecast-workspace-content {
  width: 100%;
  padding: 8px 18px 0;
}
</style>
