<script setup>
/**
 * @description 总数统计
 * @param { Array } roleCountList 列表数据
 * @param { object } item 数据
 * @param { string } item.comments 表名
 * @param { number } item.count 数量
 */
import { inject } from 'vue'
const { roleCountList } = inject('home')
</script>
<template>
  <div class="statis-wrapper" v-if="roleCountList.length">
    <div v-for="item in roleCountList" :key="item.comments" class="statis-box-common">
      <div class="info-box">
        <div class="label">{{ item.comments }}</div>
        <div class="meta">当前累计记录</div>
        <div class="count">{{ item.count }}</div>
      </div>
    </div>
  </div>
</template>
<style>
.statis-box-common {
  min-height: 136px;
  padding: 22px 24px;
  border-radius: var(--sys-radius-lg);
  background: linear-gradient(180deg, #fff 0%, #f8fbff 100%);
  border: 1px solid var(--sys-border);
  box-shadow: var(--sys-shadow-sm);
  
  .info-box {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .meta {
    color: var(--sys-text-faint);
    font-size: 12px;
  }

  .count {
    margin-top: 10px;
    color: var(--sys-text);
    font-size: 34px;
    line-height: 1;
    font-weight: 700;
  }

  .label {
    color: var(--sys-text-soft);
    font-size: 15px;
    font-weight: 600;
  }
}

</style>

