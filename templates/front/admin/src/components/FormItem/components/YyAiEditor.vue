<script setup>
/**
 * @description 安全降级版 AI 编辑器
 * 关闭外部模型直连后，回退为本地多行输入框，避免在前端暴露密钥。
 */
defineOptions({
  inheritAttrs: false,
})

const { column, ruleForm, disabled } = defineProps({
  column: {
    type: Object,
    required: true,
  },
  ruleForm: {
    type: Object,
    required: true,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const { columnName, comments } = column
</script>

<template>
  <el-input
    v-model="ruleForm[columnName]"
    type="textarea"
    :rows="6"
    :disabled="disabled"
    :placeholder="`请输入${comments}`"
  />
</template>
