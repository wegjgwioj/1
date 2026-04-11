<script setup>
/**
 * @description AI编辑器
 */

import { getListAPI } from '@/api/list'

import { onMounted, onUnmounted, ref, watch } from 'vue'

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
let { columnName, comments } = column

const divRef = ref()
let aiEditor = null

let apiKey = 'sk-4b0311f3b22e4c09917be3541c74dca8'
const baseURL = 'https://api.deepseek.com/chat/completions'

// getApiKey()
// 从config表获取apikey
async function getApiKey() {
  let res = await getListAPI('config', { limit: 1, name: 'APIKey' })
  apiKey = res.data.list[0].value
}

function initEditor() {
  // 判断cdn资源是否加载完成
  if (!AiEditor) {
    return setTimeout(() => {
      initEditor()
    }, 1000)
  }

  aiEditor = new AiEditor.AiEditor({
    element: divRef.value,
    placeholder: '请输入' + comments,
    content: ruleForm[columnName],
    editable: !disabled,
    ai: {
      models: {
        openai: {
          customUrl: baseURL,
          apiKey,
          model: 'deepseek-chat',
        },
      },
    },
    onChange: aiEditor => {
      // 监听到用编辑器内容发生变化了，控制台打印编辑器的 html 内容...

      ruleForm[columnName] = aiEditor.getHtml()
    },
  })
}
onMounted(() => {
  initEditor()
})
onUnmounted(() => {
  aiEditor && aiEditor.destroy()
  aiEditor = null
})

watch(
  () => ruleForm[columnName],
  () => {
    if (!aiEditor || ruleForm[columnName] == aiEditor.getHtml()) {
      return
    }

    aiEditor.setContent(ruleForm[columnName])
  }
)
</script>

<template>
  <div ref="divRef"></div>
</template>
<style>
.el-form-item:has(.aie-container) {
  width: 100%;
}
</style>
