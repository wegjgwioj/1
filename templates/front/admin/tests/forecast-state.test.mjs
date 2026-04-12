import test from 'node:test'
import assert from 'node:assert/strict'

import {
  createForecastForm,
  normalizeCompareResult,
  normalizeComparisonRows,
  normalizeMetricCards,
  normalizeNasaExperimentResult,
  normalizePredictionResult,
  normalizeScenarioCards,
} from '../src/views/board/forecastState.js'

test('createForecastForm returns all fields required by the prediction workspace', () => {
  const form = createForecastForm()

  assert.deepEqual(Object.keys(form), [
    'vehiclemodel',
    'batterycapacity',
    'accumulatedmileage',
    'drivingbehaviorrating',
    'drivingroute',
    'averagespeed',
    'batterylevel',
    'rapidaccelerationtimes',
    'numberofrapiddecelerations',
    'numberofspeedingincidents',
  ])
  assert.equal(form.drivingroute, '城市通勤')
  assert.equal(form.batterycapacity, 90)
})

test('normalizePredictionResult parses major factors and exposes risk tone', () => {
  const result = normalizePredictionResult({
    batterylife: 38,
    predictedpowerconsumption: 19.26,
    risklevel: '高',
    majorfactors: '["高速工况耗电偏高","存在超速事件"]',
    modelname: 'RandomForestRegressor + GradientBoostingRegressor',
    modelversion: 'ml-20260412123000',
  })

  assert.equal(result.riskTone, 'high')
  assert.equal(result.riskLabel, '高风险')
  assert.deepEqual(result.majorFactors, ['高速工况耗电偏高', '存在超速事件'])
  assert.equal(result.summaryRows[0].label, '预测电池寿命')
  assert.equal(result.recommendations.length, 3)
  assert.match(result.recommendations[0], /优先/)
})

test('normalizeMetricCards returns ordered metric cards for power and life models', () => {
  const cards = normalizeMetricCards({
    power: {
      MAE: 0.23,
      RMSE: 0.31,
      R2: 0.83,
      evaluation_mode: 'train_set_proxy',
      sample_count: 24,
    },
    life: {
      MAE: 1.2,
      RMSE: 1.8,
      R2: 0.76,
      evaluation_mode: 'holdout',
      sample_count: 24,
    },
  })

  assert.equal(cards[0].key, 'power')
  assert.equal(cards[0].title, '耗电量模型')
  assert.equal(cards[1].modeText, '留出集评估')
})

test('normalizeScenarioCards keeps scenario names and adds risk tone', () => {
  const cards = normalizeScenarioCards([
    {
      name: '稳健通勤',
      description: '平稳通勤',
      prediction: {
        batterylife: 58,
        predictedpowerconsumption: 13.2,
        risklevel: '低',
        majorfactors: ['驾驶平稳'],
      },
    },
    {
      name: '高速长途',
      description: '高速拉高能耗',
      prediction: {
        batterylife: 34,
        predictedpowerconsumption: 21.6,
        risklevel: '高',
        majorfactors: ['平均车速偏高'],
      },
    },
  ])

  assert.equal(cards[0].name, '稳健通勤')
  assert.equal(cards[0].prediction.riskTone, 'low')
  assert.equal(cards[1].prediction.riskLabel, '高风险')
})

test('normalizeScenarioCards computes delta rows against the base prediction', () => {
  const cards = normalizeScenarioCards(
    [
      {
        name: '稳健通勤',
        description: '平稳通勤',
        prediction: {
          batterylife: 58,
          predictedpowerconsumption: 13.2,
          risklevel: '低',
          majorfactors: ['驾驶平稳'],
        },
      },
      {
        name: '高速长途',
        description: '高速拉高能耗',
        prediction: {
          batterylife: 34,
          predictedpowerconsumption: 21.6,
          risklevel: '高',
          majorfactors: ['平均车速偏高'],
        },
      },
    ],
    {
      batterylife: 42,
      predictedpowerconsumption: 16.5,
      risklevel: '中',
      majorfactors: ['当前工况作为基准'],
    },
  )

  assert.equal(cards[0].deltaRows[0].label, '寿命变化')
  assert.equal(cards[0].deltaRows[0].value, '+16 月')
  assert.equal(cards[0].deltaRows[1].value, '-3.30 kWh/100km')
  assert.equal(cards[1].deltaRows[0].value, '-8 月')
  assert.equal(cards[1].deltaRows[1].value, '+5.10 kWh/100km')
})

test('normalizeComparisonRows combines traditional and neural baseline metrics by target', () => {
  const rows = normalizeComparisonRows(
    {
      power: { MAE: 0.31, RMSE: 0.42, R2: 0.76 },
      life: { MAE: 1.4, RMSE: 1.9, R2: 0.68 },
    },
    {
      power_mlp: { MAE: 0.22, RMSE: 0.35, R2: 0.83 },
      life_mlp: { MAE: 1.1, RMSE: 1.5, R2: 0.72 },
    },
  )

  assert.equal(rows[0].targetTitle, '耗电量预测')
  assert.equal(rows[0].traditional.r2, '0.760')
  assert.equal(rows[0].neural.r2, '0.830')
  assert.equal(rows[1].targetTitle, '电池寿命预测')
})

test('normalizeCompareResult exposes ML/DL cards and delta summary', () => {
  const result = normalizeCompareResult({
    ml: {
      batterylife: 42,
      predictedpowerconsumption: 16.5,
      risklevel: '中',
      majorfactors: ['当前工况作为基准'],
      modelname: 'RandomForest + GBDT',
    },
    dl: {
      batterylife: 39,
      predictedpowerconsumption: 17.8,
      risklevel: '高',
      majorfactors: ['序列模型判断高速波动更敏感'],
      modelname: 'GRURegressor',
      backend: 'pytorch',
      trainingSource: 'drivinglog_table',
      modelversion: 'dl-20260412153000',
      metrics: {
        power_dl: {
          sample_count: 24,
        },
      },
    },
    comparison: {
      power_delta: 1.3,
      life_delta: -3,
      preferred_model: 'ml',
    },
  })

  assert.equal(result.ml.riskLabel, '中风险')
  assert.equal(result.dl.riskLabel, '高风险')
  assert.equal(result.deltaRows[0].value, '+1.30 kWh/100km')
  assert.equal(result.deltaRows[1].value, '-3 月')
  assert.match(result.backendLabel, /PyTorch/i)
  assert.equal(result.trainingSourceLabel, '业务行车日志表')
  assert.equal(result.sampleCountText, '24 条样本')
  assert.equal(result.modelVersionText, 'dl-20260412153000')
})

test('normalizeCompareResult keeps placeholder values stable when comparison deltas are missing', () => {
  const result = normalizeCompareResult({
    ml: {},
    dl: {},
    comparison: {
      power_delta: null,
      life_delta: null,
      preferred_model: '--',
    },
  })

  assert.equal(result.deltaRows[0].value, '-- kWh/100km')
  assert.equal(result.deltaRows[1].value, '-- 月')
  assert.equal(result.preferredModelLabel, '--')
})

test('normalizeNasaExperimentResult builds cards and figures for frontend display', () => {
  const result = normalizeNasaExperimentResult({
    available: true,
    dataset: {
      dataset: 'NASA PCoE Battery Aging',
      source_url: 'https://example.com/nasa.zip',
      battery_count: 34,
      sample_count: 5308,
    },
    experiment: {
      model_family: 'RandomForest(SOH)+GradientBoosting(RUL)',
      split_strategy: 'group_holdout_by_battery',
      updated_at: '2026-04-12 15:03:25',
      train_battery_count: 27,
      test_battery_count: 7,
    },
    metrics: {
      soh: {
        MAE: 0.058954,
        RMSE: 0.115034,
        R2: 0.600139,
      },
      rul: {
        MAE: 13.339048,
        RMSE: 24.996156,
        R2: 0.449714,
      },
    },
    figures: [
      {
        key: 'capacity_curve',
        title: '容量衰减曲线',
        url: '/diandong5k56la1f/drivinglogforecast/nasaFigure/nasa_capacity_degradation.png',
      },
    ],
    notes: ['说明一', '说明二'],
    limitations: ['限制一'],
  })

  assert.equal(result.available, true)
  assert.equal(result.metricCards[0].title, 'SOH 健康度预测')
  assert.equal(result.metricCards[0].mae, '0.059')
  assert.equal(result.metricCards[1].title, 'RUL 剩余循环寿命预测')
  assert.equal(result.summaryRows[0].label, '电池样本')
  assert.equal(result.summaryRows[0].value, '34 组')
  assert.equal(result.splitStrategyText, '按电池分组留出评估')
  assert.equal(result.figures[0].title, '容量衰减曲线')
  assert.deepEqual(result.notes, ['说明一', '说明二'])
  assert.deepEqual(result.limitations, ['限制一'])
})
