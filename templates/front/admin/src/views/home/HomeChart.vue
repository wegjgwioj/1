
<script setup>
/**
 * item.title 图表标题
 */
import ChartEntry from '@/components/Echart/index.vue'
import { inject } from 'vue'
const { roleChartList } = inject('home')
</script>
<template>
  <!-- 图表 -->
  <ChartEntry
    v-for="item in roleChartList"
    :key="item.title"
    :data="item"
    class="chart-wrapper-common"
  />
</template>
  
