<script setup>
/**
 * @description 首页
 */
import '@/style/home.scss';
import { computed, onMounted, provide, ref } from 'vue'
import { useRouter } from 'vue-router'

import HomeChart from './HomeChart.vue'
import HomeCount from './HomeCount.vue'

import chartData from '@/components/Echart/chartData'
import { isAuth } from '@/utils/auth';
import { getCountAPI, getPageAPI } from '@/api/list'
const runIdle =
  globalThis.requestIdleCallback || ((callback) => setTimeout(callback, 1))
const router = useRouter()

// ----------------------------------
// ----------- 总数统计 --------------
// ----------------------------------
let initCountList = [
  {
    tableName: 'drivinglog',
    comments: '行车日志',
    count: 0,
  },
]
// 当前角色的总数统计 (鉴权)
initCountList = initCountList.filter(item => isAuth(item.tableName, '首页总数'))
const roleCountList = ref(initCountList)
getCountDatas()
function getCountDatas() {
  roleCountList.value.forEach(async item => {
    let res = await getCountAPI(item.tableName)
    item.count = res.data
  })
}

// ----------------------------------
// ----------- 首页图表 --------------
// ----------------------------------
// 当前角色的首页统计 (鉴权)
const roleChartList = chartData.filter(item => item.showHome).filter(item => isAuth(item.tableName, '首页统计'))
const capabilityCards = computed(() => {
  const cards = [
    {
      key: 'drivinglog',
      title: '行车日志',
      desc: '查看车辆运行记录、路线信息与基础分析结果。',
      path: '/drivinglog',
      metric: roleCountList.value.find(item => item.tableName === 'drivinglog')?.count ?? 0,
    },
    {
      key: 'vehicleknowledge',
      title: '车型知识',
      desc: '维护车型知识库，支撑日志解释与展示内容补充。',
      path: '/vehicleknowledge',
      metric: '知识补全',
    },
    {
      key: 'discussdrivinglog',
      title: '互动反馈',
      desc: '查看评论、收藏和用户反馈，追踪使用情况。',
      path: '/discussdrivinglog',
      metric: '反馈闭环',
    },
    {
      key: 'forecastWorkbench',
      title: '预测分析',
      desc: '进入预测工作台，集中展示风险等级、寿命代理值与模型结果。',
      path: '/forecastWorkbench',
      metric: '核心演示',
    },
  ]

  return cards.filter(card => card.key === 'forecastWorkbench' || isAuth(card.key, '查看'))
})


onMounted(() => {
  setTimeout(() => {
    runIdle(() => {
      // 提前加载 列表页
      import("@/views/list/list.vue");
    });
  }, 1000);
});

provide('home', {
  roleCountList,
  roleChartList,
})
</script>

<template>
  <div class="home-wrapper">
    <section class="home-overview">
      <div class="home-overview-main">
        <div class="home-kicker">系统概览</div>
        <h1 class="home-title">{{ projectName }}</h1>
        <p class="home-subtitle">
          面向电动汽车行车日志、车型知识补全与寿命预测分析的一体化工业监测平台。
        </p>
      </div>
      <div class="home-summary-panel">
        <div class="home-summary-label">当前工作焦点</div>
        <div class="home-summary-value">日志分析与预测联动</div>
        <div class="home-summary-text">
          通过运行日志、车型知识和预测分析中心，形成答辩时可直接讲述的完整业务链路。
        </div>
      </div>
    </section>

    <section class="home-capabilities">
      <div class="section-head">
        <div>
          <div class="section-title">核心能力</div>
          <div class="section-desc">从数据采集到模型输出，首页先展示系统最重要的 4 个工作入口。</div>
        </div>
      </div>
      <div class="capability-grid">
        <button
          v-for="card in capabilityCards"
          :key="card.key"
          type="button"
          class="capability-card"
          @click="router.push(card.path)"
        >
          <div class="capability-topline">
            <span class="capability-badge">{{ card.metric }}</span>
          </div>
          <div class="capability-title">{{ card.title }}</div>
          <div class="capability-desc">{{ card.desc }}</div>
        </button>
      </div>
    </section>

    <section class="home-insights">
      <div class="section-head">
        <div>
          <div class="section-title">数据概况</div>
          <div class="section-desc">优先保留真正能说明系统规模和运行状态的关键指标与图表。</div>
        </div>
      </div>
      <HomeCount />
      <HomeChart />
    </section>
  </div>
</template>
