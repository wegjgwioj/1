import test from 'node:test'
import assert from 'node:assert/strict'

import {
  createForecastForm,
  normalizeComparisonRows,
  normalizeMetricCards,
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
