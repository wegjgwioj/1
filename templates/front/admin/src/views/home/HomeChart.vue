
<script setup>
/**
 * item.title 图表标题
 */
import ChartEntry from '@/components/Echart/index.vue'
import { inject } from 'vue'
const { roleChartList } = inject('home')
</script>
<template>
  <div class="home-chart-grid" v-if="roleChartList.length">
    <ChartEntry
      v-for="item in roleChartList"
      :key="item.title"
      :data="item"
      class="chart-wrapper-common"
    />
  </div>
  <div class="home-chart-empty" v-else>
    当前角色没有可展示的首页图表，系统将优先保留核心业务入口和统计概览。
  </div>
</template>
  
