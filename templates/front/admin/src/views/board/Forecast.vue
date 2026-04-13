<script setup>
import { onMounted, ref } from 'vue'

import {
  getForecastCompareAPI,
  getForecastMetricsAPI,
  getForecastScenariosAPI,
  getNasaExperimentAPI,
  predictWorkspaceAPI,
} from '@/api/list'

import {
  normalizeCompareResult,
  createForecastForm,
  normalizeComparisonRows,
  normalizeMetricCards,
  normalizeNasaExperimentResult,
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
const compareResult = ref(null)
const scenarioCards = ref([])
const metricCards = ref([])
const comparisonRows = ref([])
const nasaExperiment = ref(normalizeNasaExperimentResult())
const updatedAt = ref('')
const modelVersion = ref('')
const isMetricsLoading = ref(false)
const isNasaLoading = ref(false)
const isSubmitting = ref(false)

function resetForm() {
  formState.value = createForecastForm()
  predictionResult.value = null
  compareResult.value = null
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

async function loadNasaExperiment() {
  isNasaLoading.value = true
  try {
    const res = await getNasaExperimentAPI(tableName)
    nasaExperiment.value = normalizeNasaExperimentResult(res.data || {})
  } catch (error) {
    nasaExperiment.value = normalizeNasaExperimentResult()
  }
  isNasaLoading.value = false
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
    const [predictionRes, scenarioRes, compareRes] = await Promise.all([
      predictWorkspaceAPI(tableName, payload),
      getForecastScenariosAPI(tableName, payload),
      getForecastCompareAPI(tableName, payload),
    ])

    predictionResult.value = normalizePredictionResult(predictionRes.data)
    compareResult.value = normalizeCompareResult(compareRes.data)
    scenarioCards.value = normalizeScenarioCards(
      scenarioRes.data.scenarios || [],
      predictionResult.value,
    )
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
  loadNasaExperiment()
})
</script>

<template>
  <div class="forecast-box">
    <div class="forecast-hero">
      <div class="hero-eyebrow">预测分析中心</div>
      <div class="hero-main">
        <div>
          <div class="hero-title">面向行车日志的风险评估与寿命预测</div>
          <div class="hero-subtitle">
            以单次工况输入为核心，统一展示寿命代理值、耗电预测、风险等级与模型实验对照。
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
        <span>更新时间：{{ updatedAt || '首次进入将自动加载模型信息' }}</span>
      </div>
    </div>

    <div class="forecast-primary-grid">
      <div class="forecast-section forecast-section-input">
        <div class="section-title">工况输入</div>
        <div class="section-note">填写一组运行参数，系统将同步给出预测结果和典型场景模拟。</div>
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

      <div class="forecast-section forecast-section-result">
        <div class="section-title">核心预测结果</div>
        <template v-if="predictionResult">
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
          <div class="result-factors">
            <div class="result-caption">建议动作</div>
            <div class="factor-list">
              <span
                class="factor-chip factor-chip-soft"
                v-for="recommendation in predictionResult.recommendations"
                :key="recommendation"
              >
                {{ recommendation }}
              </span>
            </div>
          </div>
        </template>
        <div v-else class="forecast-empty-panel">
          先输入一组工况参数并点击“立即预测”，这里会集中展示最重要的预测结论。
        </div>
      </div>
    </div>

    <div class="forecast-support-grid">
      <div class="forecast-section" v-if="scenarioCards.length">
        <div class="section-title">工况模拟</div>
        <div class="section-note">使用同一辆车的不同工况场景，辅助说明预测结果在业务语境中的变化。</div>
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
            <div class="scenario-metrics">
              <div class="scenario-metric" v-for="delta in scenario.deltaRows" :key="`${scenario.name}-${delta.label}`">
                <span>{{ delta.label }}</span>
                <strong>{{ delta.value }}</strong>
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

      <div class="forecast-section" v-if="compareResult">
        <div class="section-title">模型对照</div>
        <div class="section-note">用于展示同一工况下机器学习主模型与深度学习对比模型的输出差异。</div>
        <div class="comparison-list">
          <div class="comparison-card">
            <div class="comparison-title">预测结果</div>
            <div class="comparison-grid">
              <div class="comparison-model">
                <div class="comparison-label">机器学习主模型</div>
                <div class="comparison-metrics">
                  <span>风险 {{ compareResult.ml.riskLabel }}</span>
                  <span>寿命 {{ compareResult.ml.batterylife }} 月</span>
                  <span>耗电 {{ compareResult.ml.predictedpowerconsumption }} kWh/100km</span>
                </div>
              </div>
              <div class="comparison-model comparison-model-neural">
                <div class="comparison-label">深度学习对比模型</div>
                <div class="comparison-metrics">
                  <span>风险 {{ compareResult.dl.riskLabel }}</span>
                  <span>寿命 {{ compareResult.dl.batterylife }} 月</span>
                  <span>耗电 {{ compareResult.dl.predictedpowerconsumption }} kWh/100km</span>
                </div>
              </div>
            </div>
          </div>
          <div class="comparison-card">
            <div class="comparison-title">对比摘要</div>
            <div class="comparison-metrics">
              <span>DL 后端 {{ compareResult.backendLabel }}</span>
              <span>训练来源 {{ compareResult.trainingSourceLabel }}</span>
              <span>样本量 {{ compareResult.sampleCountText }}</span>
              <span>DL 版本 {{ compareResult.modelVersionText }}</span>
              <span>建议主看 {{ compareResult.preferredModelLabel }}</span>
            </div>
            <div class="scenario-metrics">
              <div class="scenario-metric" v-for="delta in compareResult.deltaRows" :key="delta.label">
                <span>{{ delta.label }}</span>
                <strong>{{ delta.value }}</strong>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="forecast-section">
        <div class="section-title">
          离线评估指标
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
        <div class="section-title">模型族对比</div>
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

    <div class="forecast-section forecast-section-nasa">
      <div class="section-title">
        NASA 真实寿命实验
        <span class="section-tip" v-if="isNasaLoading">加载中...</span>
      </div>
      <template v-if="nasaExperiment.available">
        <div class="nasa-topline">
          <div>
            <div class="nasa-title">{{ nasaExperiment.datasetName }}</div>
            <div class="scenario-desc">
              用公开电池老化数据把 SOH / RUL 预测链路展示出来，补齐“真实寿命实验”这一层证据。
            </div>
          </div>
          <a
            class="nasa-link"
            v-if="nasaExperiment.sourceUrl"
            :href="nasaExperiment.sourceUrl"
            target="_blank"
            rel="noreferrer"
          >
            查看数据源
          </a>
        </div>

        <div class="result-grid nasa-summary-grid">
          <div class="result-item" v-for="item in nasaExperiment.summaryRows" :key="item.label">
            <div class="result-label">{{ item.label }}</div>
            <div class="result-value">{{ item.value }}</div>
          </div>
        </div>

        <div class="comparison-metrics nasa-meta">
          <span>模型组合 {{ nasaExperiment.modelFamily }}</span>
          <span>切分方式 {{ nasaExperiment.splitStrategyText }}</span>
          <span>最近训练 {{ nasaExperiment.updatedAt }}</span>
        </div>

        <div class="metrics-list nasa-metric-list" v-if="nasaExperiment.metricCards.length">
          <div class="metric-card" v-for="card in nasaExperiment.metricCards" :key="card.key">
            <div class="metric-card-head">
              <div class="metric-card-title">{{ card.title }}</div>
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
            </div>
          </div>
        </div>

        <div class="comparison-list nasa-feature-list">
          <div class="comparison-card" v-for="item in nasaExperiment.featureRows" :key="item.label">
            <div class="comparison-title">{{ item.label }}</div>
            <div class="scenario-desc">{{ item.value }}</div>
          </div>
        </div>

        <div class="nasa-figure-grid" v-if="nasaExperiment.figures.length">
          <div class="nasa-figure-card" v-for="figure in nasaExperiment.figures" :key="figure.key">
            <img class="nasa-figure-image" :src="figure.url" :alt="figure.title" />
            <div class="scenario-name">{{ figure.title }}</div>
            <div class="scenario-desc">{{ figure.description }}</div>
          </div>
        </div>

        <div class="nasa-note-grid" v-if="nasaExperiment.notes.length || nasaExperiment.limitations.length">
          <div class="nasa-note-card">
            <div class="comparison-title">这能说明什么</div>
            <div class="factor-list">
              <span class="factor-chip factor-chip-soft" v-for="note in nasaExperiment.notes" :key="note">
                {{ note }}
              </span>
            </div>
          </div>
          <div class="nasa-note-card nasa-note-card-warning" v-if="nasaExperiment.limitations.length">
            <div class="comparison-title">当前边界</div>
            <div class="factor-list">
              <span
                class="factor-chip factor-chip-soft"
                v-for="limitation in nasaExperiment.limitations"
                :key="limitation"
              >
                {{ limitation }}
              </span>
            </div>
          </div>
        </div>
      </template>
      <div class="metrics-empty" v-else>
        NASA 实验产物尚未就绪。先运行数据准备与训练命令后，这里会展示真实寿命实验指标和结果图。
      </div>
    </div>
  </div>
</template>

<style scoped>
.forecast-box {
  display: grid;
  gap: 16px;
}

.forecast-hero,
.forecast-section {
  border-radius: var(--sys-radius-lg);
  border: 1px solid var(--sys-border);
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  box-shadow: var(--sys-shadow-sm);
}

.forecast-hero {
  padding: 22px 24px;
}

.hero-eyebrow {
  color: var(--sys-accent);
  letter-spacing: 0.12em;
  font-size: 12px;
  text-transform: uppercase;
  font-weight: 700;
}

.hero-main {
  margin-top: 12px;
  display: flex;
  gap: 16px;
  align-items: flex-start;
  justify-content: space-between;
}

.hero-title {
  color: var(--sys-text);
  font-size: 24px;
  line-height: 1.3;
  font-weight: 700;
}

.hero-subtitle {
  margin-top: 8px;
  max-width: 720px;
  color: var(--sys-text-soft);
  font-size: 13px;
  line-height: 1.65;
}

.hero-risk,
.result-risk,
.scenario-risk {
  border-radius: 999px;
  padding: 7px 12px;
  font-size: 12px;
  line-height: 1;
  white-space: nowrap;
  border: 1px solid transparent;
  font-weight: 700;
}

.hero-risk.is-high,
.result-risk.is-high,
.scenario-risk.is-high {
  color: #b93f3f;
  border-color: rgba(209, 83, 83, 0.24);
  background: rgba(209, 83, 83, 0.1);
}

.hero-risk.is-medium,
.result-risk.is-medium,
.scenario-risk.is-medium {
  color: var(--sys-warning);
  border-color: rgba(199, 134, 30, 0.24);
  background: rgba(199, 134, 30, 0.1);
}

.hero-risk.is-low,
.result-risk.is-low,
.scenario-risk.is-low {
  color: var(--sys-success);
  border-color: rgba(44, 139, 94, 0.24);
  background: rgba(44, 139, 94, 0.1);
}

.hero-risk.is-idle {
  color: var(--sys-text-soft);
  border-color: var(--sys-border);
  background: var(--sys-panel-muted);
}

.hero-meta {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px 18px;
  color: var(--sys-text-faint);
  font-size: 12px;
}

.forecast-primary-grid {
  display: grid;
  grid-template-columns: minmax(340px, 1fr) minmax(0, 1.2fr);
  gap: 16px;
}

.forecast-support-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(320px, 0.85fr);
  gap: 16px;
}

.forecast-section {
  padding: 18px 20px;
}

.section-title {
  color: var(--sys-text);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 17px;
  font-weight: 700;
}

.section-note {
  margin-top: 6px;
  color: var(--sys-text-soft);
  font-size: 12px;
  line-height: 1.6;
}

.section-tip {
  color: var(--sys-accent);
  font-size: 12px;
  font-weight: 500;
}

.forecast-form-grid {
  margin-top: 14px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.forecast-field {
  display: grid;
  gap: 6px;
}

.field-label {
  color: var(--sys-text-soft);
  font-size: 12px;
}

.field-input-wrap {
  border: 1px solid var(--sys-border);
  border-radius: 12px;
  background: #fff;
  display: flex;
  align-items: center;
  transition: border-color 0.25s ease, box-shadow 0.25s ease, transform 0.25s ease;
}

.field-input-wrap:focus-within {
  border-color: rgba(35, 117, 216, 0.4);
  box-shadow: 0 0 0 4px rgba(35, 117, 216, 0.08);
  transform: translateY(-1px);
}

.field-input {
  border: 0;
  padding: 0 11px;
  color: var(--sys-text);
  background: transparent;
  width: 100%;
  line-height: 40px;
  height: 40px;
  outline: none;
}

.field-input::-webkit-outer-spin-button,
.field-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.field-suffix {
  color: var(--sys-text-faint);
  padding-right: 12px;
  font-size: 12px;
  flex: none;
}

.forecast-actions {
  margin-top: 14px;
  display: flex;
  gap: 10px;
}

.action-btn {
  border-radius: 9px;
  padding: 0 14px;
  min-width: 0;
  line-height: 38px;
  height: 38px;
  font-size: 12px;
  border: 1px solid transparent;
  cursor: pointer;
  transition: transform 0.2s ease, opacity 0.2s ease, border-color 0.2s ease;
}

.action-btn:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.action-btn:not(:disabled):hover {
  transform: translateY(-1px);
}

.action-btn-primary {
  color: #ffffff;
  font-weight: 700;
  background: linear-gradient(135deg, var(--sys-primary), var(--sys-accent));
}

.action-btn-secondary {
  color: var(--sys-primary);
  border-color: rgba(35, 117, 216, 0.22);
  background: var(--sys-primary-soft);
}

.result-topline,
.scenario-head,
.metric-card-head {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  justify-content: space-between;
}

.result-model {
  color: var(--sys-text-soft);
  font-size: 12px;
  line-height: 1.6;
}

.result-model strong {
  color: var(--sys-text);
  display: block;
  font-size: 14px;
}

.result-grid,
.metric-card-grid,
.scenario-metrics,
.comparison-grid {
  display: grid;
  gap: 8px;
  margin-top: 12px;
}

.result-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.result-item,
.metric-cell,
.scenario-metric,
.comparison-model {
  border-radius: 12px;
  padding: 12px;
  background: #fff;
  border: 1px solid var(--sys-border);
}

.result-label,
.metric-cell span,
.scenario-metric span {
  color: var(--sys-text-faint);
  font-size: 12px;
}

.result-value,
.metric-cell strong,
.scenario-metric strong {
  margin-top: 6px;
  color: var(--sys-text);
  display: block;
  font-size: 20px;
  line-height: 1.2;
  font-weight: 700;
}

.result-value span {
  margin-left: 4px;
  font-size: 12px;
  color: var(--sys-text-faint);
}

.result-factors {
  margin-top: 14px;
}

.result-caption,
.scenario-name,
.metric-card-title,
.comparison-title {
  color: var(--sys-text);
  font-size: 14px;
  font-weight: 700;
}

.scenario-desc,
.metric-card-mode {
  color: var(--sys-text-soft);
  font-size: 12px;
  line-height: 1.6;
  margin-top: 4px;
}

.scenario-list,
.metrics-list,
.comparison-list {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

.scenario-card,
.metric-card,
.comparison-card,
.nasa-figure-card,
.nasa-note-card {
  border-radius: 14px;
  padding: 14px;
  background: var(--sys-panel-muted);
  border: 1px solid var(--sys-border);
}

.nasa-note-card-warning {
  border-color: rgba(199, 134, 30, 0.18);
  background: rgba(199, 134, 30, 0.06);
}

.comparison-model-neural {
  background: rgba(35, 117, 216, 0.06);
  border-color: rgba(35, 117, 216, 0.16);
}

.comparison-label {
  color: var(--sys-text);
  font-size: 12px;
  font-weight: 700;
}

.comparison-metrics {
  margin-top: 6px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  color: var(--sys-text-soft);
  font-size: 12px;
}

.factor-list {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.factor-chip {
  border-radius: 999px;
  padding: 5px 9px;
  color: var(--sys-primary);
  font-size: 11px;
  line-height: 1.35;
  background: var(--sys-primary-soft);
  border: 1px solid rgba(35, 117, 216, 0.12);
}

.factor-chip-soft {
  color: var(--sys-text-soft);
  background: #ffffff;
  border-color: var(--sys-border);
}

.metrics-empty,
.forecast-empty-panel {
  color: var(--sys-text-soft);
  line-height: 1.7;
  font-size: 13px;
}

.forecast-empty-panel {
  min-height: 220px;
  margin-top: 14px;
  border-radius: 16px;
  border: 1px dashed var(--sys-border-strong);
  background: var(--sys-panel-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  text-align: center;
}

.nasa-topline {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  justify-content: space-between;
}

.nasa-title {
  color: var(--sys-text);
  font-size: 18px;
  font-weight: 700;
}

.nasa-link {
  color: var(--sys-primary);
  font-size: 12px;
  line-height: 1.4;
  white-space: nowrap;
  text-decoration: none;
  border-bottom: 1px solid rgba(35, 117, 216, 0.26);
}

.nasa-link:hover {
  opacity: 0.85;
}

.nasa-meta,
.nasa-feature-list,
.nasa-note-grid,
.nasa-figure-grid {
  margin-top: 12px;
}

.nasa-figure-grid {
  display: grid;
  gap: 8px;
}

.forecast-support-grid > .forecast-section:first-child {
  grid-column: 1 / -1;
}

.forecast-section-nasa {
  background: linear-gradient(180deg, #fbfcfe 0%, #f5f8fc 100%);
}

.nasa-figure-image {
  border-radius: 12px;
  margin-bottom: 12px;
  display: block;
  background: rgba(255, 255, 255, 0.03);
  width: 100%;
  height: auto;
  object-fit: cover;
}

@media (max-width: 1100px) {
  .forecast-primary-grid,
  .forecast-form-grid,
  .result-grid,
  .forecast-support-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .hero-main,
  .result-topline,
  .scenario-head,
  .metric-card-head,
  .nasa-topline {
    flex-direction: column;
  }
}
</style>
