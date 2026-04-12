<script setup>
import { onMounted, ref } from 'vue'

import {
  getForecastMetricsAPI,
  getForecastScenariosAPI,
  predictWorkspaceAPI,
} from '@/api/list'

import {
  createForecastForm,
  normalizeComparisonRows,
  normalizeMetricCards,
  normalizePredictionResult,
  normalizeScenarioCards,
} from './forecastState'

const tableName = 'drivinglogforecast'

const formFields = [
  {
    key: 'vehiclemodel',
    label: '车辆型号',
    type: 'text',
    placeholder: '如：Model-A',
  },
  {
    key: 'drivingroute',
    label: '行驶路线',
    type: 'text',
    placeholder: '如：城市通勤',
  },
  {
    key: 'batterycapacity',
    label: '电池容量',
    type: 'number',
    min: 1,
    step: 1,
    suffix: 'kWh',
  },
  {
    key: 'accumulatedmileage',
    label: '累计里程',
    type: 'number',
    min: 0,
    step: 1,
    suffix: 'km',
  },
  {
    key: 'drivingbehaviorrating',
    label: '驾驶评分',
    type: 'number',
    min: 0,
    max: 100,
    step: 1,
    suffix: '分',
  },
  {
    key: 'averagespeed',
    label: '平均车速',
    type: 'number',
    min: 0,
    step: 1,
    suffix: 'km/h',
  },
  {
    key: 'batterylevel',
    label: '电池余量',
    type: 'number',
    min: 0,
    max: 100,
    step: 1,
    suffix: '%',
  },
  {
    key: 'rapidaccelerationtimes',
    label: '急加速次数',
    type: 'number',
    min: 0,
    step: 1,
  },
  {
    key: 'numberofrapiddecelerations',
    label: '急减速次数',
    type: 'number',
    min: 0,
    step: 1,
  },
  {
    key: 'numberofspeedingincidents',
    label: '超速次数',
    type: 'number',
    min: 0,
    step: 1,
  },
]

const formState = ref(createForecastForm())
const predictionResult = ref(null)
const scenarioCards = ref([])
const metricCards = ref([])
const comparisonRows = ref([])
const updatedAt = ref('')
const modelVersion = ref('')
const isMetricsLoading = ref(false)
const isSubmitting = ref(false)

function resetForm() {
  formState.value = createForecastForm()
  predictionResult.value = null
  scenarioCards.value = []
}

function applyMetricState(metrics, comparisonMetrics = {}, extra = {}) {
  metricCards.value = normalizeMetricCards(metrics)
  comparisonRows.value = normalizeComparisonRows(metrics, comparisonMetrics)
  updatedAt.value = extra.updatedAt || updatedAt.value
  modelVersion.value = extra.modelVersion || modelVersion.value
}

async function loadMetrics() {
  isMetricsLoading.value = true
  try {
    const res = await getForecastMetricsAPI(tableName)
    applyMetricState(res.data.metrics || {}, res.data.comparison_metrics || {}, {
      updatedAt: res.data.updated_at,
      modelVersion: res.data.modelversion,
    })
  } catch (error) {
    metricCards.value = []
  }
  isMetricsLoading.value = false
}

async function forecast() {
  if (isSubmitting.value) {
    return
  }
  isSubmitting.value = true
  ElMessage.info({
    message: '正在生成预测结果和场景对比...',
    duration: 0,
  })
  try {
    const payload = { ...formState.value }
    const [predictionRes, scenarioRes] = await Promise.all([
      predictWorkspaceAPI(tableName, payload),
      getForecastScenariosAPI(tableName, payload),
    ])

    predictionResult.value = normalizePredictionResult(predictionRes.data)
    scenarioCards.value = normalizeScenarioCards(scenarioRes.data.scenarios || [])
    applyMetricState(predictionRes.data.metrics || {}, predictionRes.data.comparison_metrics || {}, {
      updatedAt: predictionRes.data.updated_at || scenarioRes.data.updated_at,
      modelVersion: predictionRes.data.modelversion || scenarioRes.data.modelversion,
    })
    ElMessage.closeAll()
    ElMessage.success('预测完成，已更新场景模拟结果')
  } catch (error) {
    ElMessage.closeAll()
    ElMessage.error(error.message || error.msg || '预测失败')
  }
  isSubmitting.value = false
}

onMounted(() => {
  loadMetrics()
})
</script>

<template>
  <div class="forecast-box">
    <div class="forecast-hero">
      <div class="hero-eyebrow">行车工况预测工作台</div>
      <div class="hero-main">
        <div>
          <div class="hero-title">输入一组工况，立即返回寿命、能耗和风险判断</div>
          <div class="hero-subtitle">
            当前页面直接调用机器学习模型，并同步给出 3 种典型场景的对比结果。
          </div>
        </div>
        <div
          class="hero-risk"
          :class="predictionResult ? `is-${predictionResult.riskTone}` : 'is-idle'"
        >
          {{ predictionResult ? predictionResult.riskLabel : '待预测' }}
        </div>
      </div>
      <div class="hero-meta">
        <span>模型版本：{{ modelVersion || '尚未加载' }}</span>
        <span>更新时间：{{ updatedAt || '首次进入将自动训练/加载' }}</span>
      </div>
    </div>

    <div class="forecast-section">
      <div class="section-title">工况输入</div>
      <div class="forecast-form-grid">
        <label class="forecast-field" v-for="field in formFields" :key="field.key">
          <span class="field-label">{{ field.label }}</span>
          <div class="field-input-wrap">
            <input
              class="field-input"
              v-model="formState[field.key]"
              :type="field.type"
              :placeholder="field.placeholder || field.label"
              :min="field.min"
              :max="field.max"
              :step="field.step"
            />
            <span class="field-suffix" v-if="field.suffix">{{ field.suffix }}</span>
          </div>
        </label>
      </div>
      <div class="forecast-actions">
        <button class="action-btn action-btn-primary" :disabled="isSubmitting" @click="forecast">
          {{ isSubmitting ? '预测中...' : '立即预测' }}
        </button>
        <button class="action-btn action-btn-secondary" :disabled="isSubmitting" @click="resetForm">
          恢复示例
        </button>
      </div>
    </div>

    <transition name="forecast-fade">
      <div class="forecast-section forecast-section-result" v-if="predictionResult">
        <div class="section-title">单次预测结果</div>
        <div class="result-topline">
          <div class="result-model">
            <span>模型：</span>
            <strong>{{ predictionResult.modelname || '当前模型' }}</strong>
          </div>
          <div class="result-risk" :class="`is-${predictionResult.riskTone}`">
            {{ predictionResult.riskLabel }}
          </div>
        </div>
        <div class="result-grid">
          <div class="result-item" v-for="item in predictionResult.summaryRows" :key="item.label">
            <div class="result-label">{{ item.label }}</div>
            <div class="result-value">
              {{ item.value }}<span v-if="item.unit">{{ item.unit }}</span>
            </div>
          </div>
        </div>
        <div class="result-factors">
          <div class="result-caption">主要影响因素</div>
          <div class="factor-list">
            <span class="factor-chip" v-for="factor in predictionResult.majorFactors" :key="factor">
              {{ factor }}
            </span>
          </div>
        </div>
      </div>
    </transition>

    <div class="forecast-section" v-if="scenarioCards.length">
      <div class="section-title">场景模拟对比</div>
      <div class="scenario-list">
        <div class="scenario-card" v-for="scenario in scenarioCards" :key="scenario.name">
          <div class="scenario-head">
            <div>
              <div class="scenario-name">{{ scenario.name }}</div>
              <div class="scenario-desc">{{ scenario.description }}</div>
            </div>
            <span class="scenario-risk" :class="`is-${scenario.prediction.riskTone}`">
              {{ scenario.prediction.riskLabel }}
            </span>
          </div>
          <div class="scenario-metrics">
            <div class="scenario-metric">
              <span>电池寿命</span>
              <strong>{{ scenario.prediction.batterylife }} 月</strong>
            </div>
            <div class="scenario-metric">
              <span>预测耗电</span>
              <strong>{{ scenario.prediction.predictedpowerconsumption }} kWh/100km</strong>
            </div>
          </div>
          <div class="factor-list">
            <span
              class="factor-chip factor-chip-soft"
              v-for="factor in scenario.prediction.majorFactors"
              :key="`${scenario.name}-${factor}`"
            >
              {{ factor }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <div class="forecast-section">
      <div class="section-title">
        模型指标
        <span class="section-tip" v-if="isMetricsLoading">加载中...</span>
      </div>
      <div class="metrics-list" v-if="metricCards.length">
        <div class="metric-card" v-for="card in metricCards" :key="card.key">
          <div class="metric-card-head">
            <div class="metric-card-title">{{ card.title }}</div>
            <div class="metric-card-mode">{{ card.modeText }}</div>
          </div>
          <div class="metric-card-grid">
            <div class="metric-cell">
              <span>MAE</span>
              <strong>{{ card.mae }}</strong>
            </div>
            <div class="metric-cell">
              <span>RMSE</span>
              <strong>{{ card.rmse }}</strong>
            </div>
            <div class="metric-cell">
              <span>R²</span>
              <strong>{{ card.r2 }}</strong>
            </div>
            <div class="metric-cell">
              <span>样本量</span>
              <strong>{{ card.sampleCount }}</strong>
            </div>
          </div>
        </div>
      </div>
      <div class="metrics-empty" v-else>
        指标尚未返回。点击上方“立即预测”后，这里会同步展示当前模型评估结果。
      </div>
    </div>

    <div class="forecast-section" v-if="comparisonRows.length">
      <div class="section-title">模型对比</div>
      <div class="comparison-list">
        <div class="comparison-card" v-for="row in comparisonRows" :key="row.targetTitle">
          <div class="comparison-title">{{ row.targetTitle }}</div>
          <div class="comparison-grid">
            <div class="comparison-model" v-if="row.traditional">
              <div class="comparison-label">传统机器学习</div>
              <div class="comparison-metrics">
                <span>MAE {{ row.traditional.mae }}</span>
                <span>RMSE {{ row.traditional.rmse }}</span>
                <span>R² {{ row.traditional.r2 }}</span>
              </div>
            </div>
            <div class="comparison-model comparison-model-neural" v-if="row.neural">
              <div class="comparison-label">神经网络基线</div>
              <div class="comparison-metrics">
                <span>MAE {{ row.neural.mae }}</span>
                <span>RMSE {{ row.neural.rmse }}</span>
                <span>R² {{ row.neural.r2 }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
