<script setup></script>
<template>
  <el-button class="login-btn" native-type="submit" type="primary">登录</el-button>
</template>
<style>
.login-btn {
  border: 0px solid transparent;
  border-radius: 45px;
  padding: 4px 15px;
  margin-bottom: 20px;
  width: 100%;
  font-size: 24px;
  height: 45px;

  background: var(--btn-bg-color-);
  box-shadow: 0 4px 15px rgb(from var(--btn-bg-color-) r g b / 0.3);
  position: relative;
  overflow: visible;

  &::before,
  &::after {
    content: '';
    position: absolute;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.8);
    opacity: 0;
    transition: all 0.4s;
  }

  &::before {
    top: 20%;
    left: 20%;
  }

  &::after {
    bottom: 20%;
    right: 20%;
  }

  &:hover {
    background: var(--btn-bg-hover-color-);
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgb(from var(--btn-bg-color-) r g b / 0.5);

    &::before {
      opacity: 1;
      transform: translate(-20px, -20px) scale(2);
    }

    &::after {
      opacity: 1;
      transform: translate(20px, 20px) scale(2);
    }
  }

  &:active {
    transform: translateY(-1px) scale(0.98);
  }
}
</style>

