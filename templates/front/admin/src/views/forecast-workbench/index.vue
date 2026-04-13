<script setup>
import { useRouter } from 'vue-router'

import Forecast from '@/views/board/Forecast.vue'

const router = useRouter()
</script>

<template>
  <div class="forecast-workspace-page">
    <div class="forecast-workspace-shell">
      <div class="forecast-workspace-head">
        <div class="forecast-workspace-head-main">
          <div>
            <div class="forecast-workspace-kicker">预测分析中心</div>
            <div class="forecast-workspace-title">电池寿命预测工作台</div>
          </div>
          <div class="forecast-workspace-desc">
            当前页面用于串联工况输入、核心预测、离线指标与公开实验结果，作为答辩主分析页面。
          </div>
        </div>
        <div class="forecast-workspace-actions">
          <el-button text @click="router.push('/drivinglogforecast')">返回预测记录</el-button>
          <el-button type="primary" @click="router.push('/home')">返回首页</el-button>
        </div>
      </div>

      <div class="forecast-workspace-content">
        <Forecast />
      </div>
    </div>
  </div>
</template>

<style scoped>
.forecast-workspace-page {
  min-height: 100%;
}

.forecast-workspace-shell {
  display: grid;
  gap: 16px;
}

.forecast-workspace-head {
  border-radius: var(--sys-radius-lg);
  border: 1px solid var(--sys-border);
  background: rgba(255, 255, 255, 0.88);
  box-shadow: var(--sys-shadow-sm);
  padding: 18px 22px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.forecast-workspace-head-main {
  display: grid;
  gap: 10px;
}

.forecast-workspace-kicker {
  color: var(--sys-accent);
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  font-weight: 700;
}

.forecast-workspace-title {
  margin-top: 6px;
  color: var(--sys-text);
  font-size: 24px;
  font-weight: 700;
}

.forecast-workspace-desc {
  max-width: 760px;
  color: var(--sys-text-soft);
  font-size: 13px;
  line-height: 1.65;
}

.forecast-workspace-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.forecast-workspace-content {
  width: 100%;
}

@media (max-width: 900px) {
  .forecast-workspace-head {
    flex-direction: column;
  }
}
</style>
