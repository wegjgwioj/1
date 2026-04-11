<script setup>
/**
 * @description 导入、上传模板
 */
import base from '@/utils/base'
import { computed } from 'vue'

defineOptions({
  inheritAttrs: false,
})
const visible = defineModel()
const { data, tableName } = defineProps(['data', 'tableName'])
let { type, title } = data
const emits = defineEmits(['fetchData'])

const headers = {
  Token: localStorage.getItem('Token'),
}

// 上传文件的API地址
// 根据type判断是导入还是上传模板
const action = computed(() => {
  return type == 'import'
    ? base.get().url + tableName + '/importExcel'
    : base.get().url + 'file/upload?type=' + tableName + '_template'
})

const exceedEvent = () => {
  ElMessage({
    message: '只能上传一个文件!',
    type: 'error',
  })
}

const successEvent = (response, uploadFile, uploadFiles) => {
  if (response.code == 0) {
    // 这里可以添加上传成功后的逻辑
    ElMessage.success(title + ' 成功!')
    visible.value = false
    emits('fetchData')
    return
  }

  let msg = response.msg || response.message || '未知错误'
  msg = title +  '失败:' + msg
  ElMessage.error(msg)
}
</script>

<template>
  <el-upload
    class="upload-wrapper"
    drag
    :action="action"
    :limit="1"
    accept=".xls,.xlsx"
    :headers="headers"
    :on-exceed="exceedEvent"
    :on-success="successEvent"
  >
    <el-icon class="el-icon--upload"><upload-filled /></el-icon>
    <div class="el-upload__text">
      拖拽上传文件 或
      <em>点击上传</em>
    </div>
  </el-upload>
</template>
