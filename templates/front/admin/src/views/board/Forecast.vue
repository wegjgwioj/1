<script setup>
import { ref } from 'vue'
import { getInfoAPI, predictAPI, saveAPI } from '@/api/list'

const tableName = 'drivinglogforecast'
const inputColumns = [
  {
    cloumnName: 'vehiclemodel',
    comments: '车辆型号',
  },
  {
    cloumnName: 'batterycapacity',
    comments: '电池容量',
  },
  {
    cloumnName: 'accumulatedmileage',
    comments: '累计行驶里程',
  },
  {
    cloumnName: 'drivingbehaviorrating',
    comments: '驾驶行为评分',
  },
]
const targetColumns = [
  {
    cloumnName: 'batterylife',
    comments: '电池寿命',
  },
]
const ruleForm = ref({
  vehiclemodel: '',
  batterycapacity: '',
  accumulatedmileage: '',
  drivingbehaviorrating: '',
  batterylife: '',
})

const isLoading = ref(false)
async function forecast() {
  if (isLoading.value) {
    return
  }
  isLoading.value = true
  try {
    ElMessage.info({
      message: '预测中... ...',
      duration: 0,
    })
    let data = {
      ...ruleForm.value,
    }
    delete data.id
    
    // 加一条数据
    let { data: id } = await saveAPI(tableName, data)

    // 预测
    data.id = id
    targetColumns.forEach(column => {
      delete data[column.cloumnName]
    })
    await predictAPI(tableName, data)

    // 更新预测结果
    let res = await getInfoAPI(tableName, id)

    ruleForm.value = res.data
    ElMessage.closeAll()
    ElMessage.success('数据预测完成')
  } catch (error) {
    ElMessage.closeAll()
    ElMessage.error('数据预测失败')
    console.log(error)
  }
  isLoading.value = false
}
</script>
<template>
  <div class="forecast-box">
    <!-- 表单字段输入列表 -->
    <div class="item" v-for="column in inputColumns" :key="column.cloumnName">
      <div class="label">
        {{ column.comments }}
      </div>
      <input class="input" v-model="ruleForm[column.cloumnName]" :placeholder="column.comments" />
    </div>

    <!-- 预测字段列表 -->
    <div class="text" v-for="column in targetColumns" :key="column.cloumnName">
      预测{{ column.comments }}：{{ ruleForm[column.cloumnName] }}
    </div>

    <!-- 按钮 -->
    <div class="btn" @click="forecast">立即预测</div>
  </div>
</template>
