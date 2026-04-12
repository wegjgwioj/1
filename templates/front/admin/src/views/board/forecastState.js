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

export function normalizeScenarioCards(scenarios = []) {
  return scenarios.map((scenario) => ({
    ...scenario,
    prediction: normalizePredictionResult(scenario.prediction),
  }))
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
