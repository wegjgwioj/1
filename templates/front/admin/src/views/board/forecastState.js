const DEFAULT_FORECAST_FORM = {
  vehiclemodel: 'Model-A',
  batterycapacity: 90,
  accumulatedmileage: 160,
  drivingbehaviorrating: 82,
  drivingroute: '城市通勤',
  averagespeed: 58,
  batterylevel: 70,
  rapidaccelerationtimes: 1,
  numberofrapiddecelerations: 1,
  numberofspeedingincidents: 0,
}

const RISK_META = {
  高: { tone: 'high', label: '高风险' },
  中: { tone: 'medium', label: '中风险' },
  低: { tone: 'low', label: '低风险' },
}

const METRIC_META = {
  power: {
    title: '耗电量模型',
    unit: 'kWh/100km',
  },
  life: {
    title: '电池寿命模型',
    unit: '月',
  },
}

const EVALUATION_MODE_TEXT = {
  holdout: '留出集评估',
  train_set_proxy: '训练集代理评估',
}

const COMPARISON_META = [
  {
    targetTitle: '耗电量预测',
    traditionalKey: 'power',
    neuralKey: 'power_mlp',
  },
  {
    targetTitle: '电池寿命预测',
    traditionalKey: 'life',
    neuralKey: 'life_mlp',
  },
]

const BACKEND_LABELS = {
  pytorch_gru: 'PyTorch GRU',
  sklearn_mlp_fallback: 'MLP 回退模型',
  pytorch: 'PyTorch',
}

const TRAINING_SOURCE_LABELS = {
  drivinglog_table: '业务行车日志表',
  raw_excel: '原始 21507 条工况表',
}

const NASA_SPLIT_STRATEGY_TEXT = {
  group_holdout_by_battery: '按电池分组留出评估',
  train_set_proxy: '训练集代理评估',
}

function toFixedNumber(value, digits = 2) {
  const numeric = Number(value)
  if (Number.isNaN(numeric)) {
    return '--'
  }
  return numeric.toFixed(digits)
}

function normalizeRisk(riskLevel) {
  return RISK_META[riskLevel] || { tone: 'medium', label: '待评估' }
}

function parseMajorFactors(majorFactors) {
  if (Array.isArray(majorFactors)) {
    return majorFactors.filter(Boolean)
  }
  if (typeof majorFactors === 'string' && majorFactors.trim()) {
    try {
      const parsed = JSON.parse(majorFactors)
      if (Array.isArray(parsed)) {
        return parsed.filter(Boolean)
      }
    } catch (error) {
      return majorFactors
        .split(/[；;、\n]/)
        .map((item) => item.trim())
        .filter(Boolean)
    }
  }
  return []
}

function buildRecommendations(result, risk) {
  const recommendations = []

  if (risk.tone === 'high') {
    recommendations.push('优先检查电池健康状态，并尽快复核近期高能耗工况。')
  } else if (risk.tone === 'medium') {
    recommendations.push('优先优化当前路线与驾驶习惯，避免风险继续升高。')
  } else {
    recommendations.push('优先保持当前平稳工况，按周期复查电池健康趋势。')
  }

  if (Number(result.predictedpowerconsumption) >= 18) {
    recommendations.push('降低高速巡航和急加速频次，有助于压低百公里耗电。')
  } else {
    recommendations.push('当前耗电表现较稳，可继续维持柔和加速和匀速行驶。')
  }

  if (Number(result.batterylife) <= 48) {
    recommendations.push('建议结合保养记录安排电池诊断，关注寿命衰减速度。')
  } else {
    recommendations.push('当前寿命预测相对平稳，建议继续关注累计里程增长后的变化。')
  }

  return recommendations.slice(0, 3)
}

function formatDelta(value, digits = 0) {
  const numeric = Number(value)
  if (Number.isNaN(numeric)) {
    return '--'
  }
  const prefix = numeric > 0 ? '+' : ''
  return `${prefix}${numeric.toFixed(digits)}`
}

function formatDeltaWithUnit(value, digits, unit) {
  if (value === null || value === undefined || value === '') {
    return `-- ${unit}`
  }
  const numeric = Number(value)
  if (Number.isNaN(numeric)) {
    return `-- ${unit}`
  }
  return `${formatDelta(numeric, digits)} ${unit}`
}

function formatCountWithUnit(value, unit) {
  const numeric = Number(value)
  if (Number.isNaN(numeric)) {
    return '--'
  }
  return `${numeric} ${unit}`
}

export function createForecastForm() {
  return { ...DEFAULT_FORECAST_FORM }
}

export function normalizePredictionResult(result = {}) {
  const risk = normalizeRisk(result.risklevel)
  const majorFactors = parseMajorFactors(result.majorfactors)
  return {
    ...result,
    riskTone: risk.tone,
    riskLabel: risk.label,
    majorFactors,
    recommendations: buildRecommendations(result, risk),
    summaryRows: [
      {
        label: '预测电池寿命',
        value: result.batterylife ?? '--',
        unit: '月',
      },
      {
        label: '预测耗电量',
        value: toFixedNumber(result.predictedpowerconsumption),
        unit: 'kWh/100km',
      },
      {
        label: '风险等级',
        value: risk.label,
        unit: '',
      },
    ],
  }
}

export function normalizeMetricCards(metrics = {}) {
  return ['power', 'life']
    .filter((key) => metrics[key])
    .map((key) => ({
      key,
      title: METRIC_META[key].title,
      unit: METRIC_META[key].unit,
      mae: toFixedNumber(metrics[key].MAE, 3),
      rmse: toFixedNumber(metrics[key].RMSE, 3),
      r2: toFixedNumber(metrics[key].R2, 3),
      sampleCount: metrics[key].sample_count ?? '--',
      modeText: EVALUATION_MODE_TEXT[metrics[key].evaluation_mode] || '当前评估',
    }))
}

export function normalizeScenarioCards(scenarios = [], basePrediction = null) {
  return scenarios.map((scenario) => ({
    ...scenario,
    prediction: normalizePredictionResult(scenario.prediction),
    deltaRows: basePrediction
      ? [
          {
            label: '寿命变化',
            value: `${formatDelta(
              Number(scenario.prediction?.batterylife) - Number(basePrediction.batterylife),
              0,
            )} 月`,
          },
          {
            label: '耗电变化',
            value: `${formatDelta(
              Number(scenario.prediction?.predictedpowerconsumption) -
                Number(basePrediction.predictedpowerconsumption),
              2,
            )} kWh/100km`,
          },
        ]
      : [],
  }))
}

export function normalizeCompareResult(result = {}) {
  const ml = normalizePredictionResult(result.ml || {})
  const dl = normalizePredictionResult(result.dl || {})
  const comparison = result.comparison || {}
  const backendLabel = BACKEND_LABELS[result.dl?.backend] || result.dl?.backend || '未返回'
  const trainingSource = result.dl?.trainingSource || '--'
  const sampleCount =
    result.dl?.metrics?.power_dl?.sample_count ??
    result.dl?.metrics?.life_dl?.sample_count ??
    '--'

  return {
    ml,
    dl,
    backendLabel,
    trainingSource,
    trainingSourceLabel: TRAINING_SOURCE_LABELS[trainingSource] || trainingSource,
    sampleCountText: sampleCount === '--' ? '--' : `${sampleCount} 条样本`,
    modelVersionText: result.dl?.modelversion || '--',
    preferredModel: comparison.preferred_model || '--',
    preferredModelLabel:
      comparison.preferred_model === 'dl'
        ? '深度学习对比结果'
        : comparison.preferred_model === 'ml'
          ? '机器学习主模型结果'
          : '--',
    deltaRows: [
      {
        label: 'DL 相比 ML 耗电差值',
        value: formatDeltaWithUnit(comparison.power_delta, 2, 'kWh/100km'),
      },
      {
        label: 'DL 相比 ML 寿命差值',
        value: formatDeltaWithUnit(comparison.life_delta, 0, '月'),
      },
    ],
  }
}

export function normalizeNasaExperimentResult(result = {}) {
  const dataset = result.dataset || {}
  const experiment = result.experiment || {}
  const metrics = result.metrics || {}

  return {
    available: Boolean(result.available),
    datasetName: dataset.dataset || experiment.dataset || 'NASA PCoE Battery Aging',
    sourceUrl: dataset.source_url || '',
    modelFamily: experiment.model_family || '--',
    updatedAt: experiment.updated_at || dataset.generated_at || '--',
    splitStrategyText:
      NASA_SPLIT_STRATEGY_TEXT[experiment.split_strategy] || experiment.split_strategy || '--',
    summaryRows: [
      {
        label: '电池样本',
        value: formatCountWithUnit(dataset.battery_count ?? experiment.battery_count, '组'),
      },
      {
        label: '循环样本',
        value: formatCountWithUnit(dataset.sample_count ?? experiment.sample_count, '条'),
      },
      {
        label: '训练电池',
        value: formatCountWithUnit(experiment.train_battery_count, '组'),
      },
      {
        label: '测试电池',
        value: formatCountWithUnit(experiment.test_battery_count, '组'),
      },
    ],
    metricCards: [
      metrics.soh
        ? {
            key: 'soh',
            title: 'SOH 健康度预测',
            mae: toFixedNumber(metrics.soh.MAE, 3),
            rmse: toFixedNumber(metrics.soh.RMSE, 3),
            r2: toFixedNumber(metrics.soh.R2, 3),
          }
        : null,
      metrics.rul
        ? {
            key: 'rul',
            title: 'RUL 剩余循环寿命预测',
            mae: toFixedNumber(metrics.rul.MAE, 3),
            rmse: toFixedNumber(metrics.rul.RMSE, 3),
            r2: toFixedNumber(metrics.rul.R2, 3),
          }
        : null,
    ].filter(Boolean),
    featureRows: [
      {
        label: 'SOH 特征',
        value: (experiment.feature_columns?.soh || []).join(' / ') || '--',
      },
      {
        label: 'RUL 特征',
        value: (experiment.feature_columns?.rul || []).join(' / ') || '--',
      },
    ],
    figures: (result.figures || []).map((figure) => ({
      key: figure.key,
      title: figure.title || figure.key,
      description: figure.description || '',
      url: figure.url || '',
    })),
    notes: Array.isArray(result.notes) ? result.notes.filter(Boolean) : [],
    limitations: Array.isArray(result.limitations) ? result.limitations.filter(Boolean) : [],
  }
}

export function normalizeComparisonRows(metrics = {}, comparisonMetrics = {}) {
  return COMPARISON_META.filter(
    (item) => metrics[item.traditionalKey] || comparisonMetrics[item.neuralKey],
  ).map((item) => ({
    targetTitle: item.targetTitle,
    traditional: metrics[item.traditionalKey]
      ? {
          mae: toFixedNumber(metrics[item.traditionalKey].MAE, 3),
          rmse: toFixedNumber(metrics[item.traditionalKey].RMSE, 3),
          r2: toFixedNumber(metrics[item.traditionalKey].R2, 3),
        }
      : null,
    neural: comparisonMetrics[item.neuralKey]
      ? {
          mae: toFixedNumber(comparisonMetrics[item.neuralKey].MAE, 3),
          rmse: toFixedNumber(comparisonMetrics[item.neuralKey].RMSE, 3),
          r2: toFixedNumber(comparisonMetrics[item.neuralKey].R2, 3),
        }
      : null,
  }))
}
