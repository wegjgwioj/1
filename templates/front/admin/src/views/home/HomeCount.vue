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
    <div v-for="(item, index) in roleCountList" :key="item.comments" class="statis-box-common" :class="'statis-box' + (index + 1)">
      <!-- 图标 -->
      <div class="icon-box" :class="'icon-box' + (index + 1)"></div>

      <!-- 文字 -->
      <div class="info-box">
        <div class="label">
          {{ item.comments }}
          <span>总数</span>
        </div>
        <div class="count">{{ item.count }}</div>
      </div>
      <div :class="'right-img' + (index + 1)">
       </div>
    </div>
  </div>
</template>
<style>
.statis-box-common {
    flex: none;
    display: flex;
    flex-wrap: wrap;
    box-shadow: none;
    padding: 30px 20px;
    border-radius: 4px;
    background: url(http://codegen.caihongy.cn/20251029/b64c87bc2e244167a420cba559adde1e.png) no-repeat center / 100% 100%;
    width: calc(25% - 15px);
    height:215px;
    padding:30px;
  .icon {
    color: var(--btn-bg-color-);
    font-size: 46px;
  }

  .info-box {
    flex: 1 1 auto;
    width: auto;
    display: flex;
    align-items: flex-start;
    flex-direction: column;
    justify-content: center;
    order: 1;
    gap: 10px;

    .count {
      margin: 0;
      font-size: 26px;
      color: #F95F3F;
      font-weight: bold;
      height: auto;

      span {
        font-size: 14px;
        font-weight: 500;
      }
    }

    .label {
      font-size: 26px;
      order:1;
      color: #F95F3F;
      height: auto;
    }
  }
}
.statis-box2{
  background: url(http://codegen.caihongy.cn/20251029/5d2960f7a71e4cc4bb5e61045cadf8cc.png) no-repeat center / 100% 100%;
}
.statis-box3{
  background: url(http://codegen.caihongy.cn/20251029/3eeadc4914ec4e94aa6655fa194c8e84.png) no-repeat center / 100% 100%;
}
.statis-box4{
  background: url(http://codegen.caihongy.cn/20251029/f5613b2a806e44919c9c75221a7f8c1c.png) no-repeat center / 100% 100%;
}

</style>

