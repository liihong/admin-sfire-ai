<template>
  <div class="login-container flx-center">
    <div class="login-box">
      <!-- 改造后的左侧区域 -->
      <div class="login-left">
        <!-- 动态粒子背景容器 -->
        <div class="particle-bg" ref="particleRef"></div>
        
        <!-- 品牌视觉中心 -->
        <div class="left-content">
          <!-- 纯CSS绘制的动态Logo -->
          <div class="brand-logo-anim">
            <div class="circle-dashed"></div>
            <div class="circle-solid"></div>
            <div class="core-point"></div>
            <div class="code-tag">&lt;/&gt;</div>
          </div>

          <h1 class="brand-title">HUOYUAN TECH</h1>
          <div class="brand-divider"></div>
          <p class="brand-slogan">星星之火 · 可以燎原</p>
        </div>
      </div>

      <!-- 右侧表单区域 -->
      <div class="login-form">
        <div class="login-logo">
          <img class="login-icon" src="@/assets/images/logo.svg" alt="" />
          <h2 class="logo-text">火源AI 后台管理</h2>
        </div>
        <LoginForm />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts" name="login">
import { ref, onMounted, onUnmounted } from 'vue';
import LoginForm from "./components/LoginForm.vue";
import SwitchDark from "@/components/SwitchDark/index.vue";

// --- 粒子特效逻辑 ---
const particleRef = ref<HTMLElement | null>(null);
let intervalId: any = null;

onMounted(() => {
  const container = particleRef.value;
  if (!container) return;

  const createSpark = () => {
    // 确保组件未卸载
    if (!container) return;
    
    const spark = document.createElement('div');
    spark.classList.add('spark');
    
    // 随机大小 (1px - 4px)
    const size = Math.random() * 3 + 1;
    spark.style.width = `${size}px`;
    spark.style.height = `${size}px`;
    
    // 随机水平位置 (0% - 100%)
    spark.style.left = `${Math.random() * 100}%`;
    
    // 随机动画时长 (3s - 8s)
    const duration = 3 + Math.random() * 5;
    spark.style.animationDuration = `${duration}s`;
    
    container.appendChild(spark);

    // 动画结束后移除DOM
    setTimeout(() => {
      if (spark.parentNode === container) {
        container.removeChild(spark);
      }
    }, duration * 1000);
  };

  // 初始化先生成一批，避免空白
  for (let i = 0; i < 15; i++) {
    setTimeout(createSpark, Math.random() * 2000);
  }
  
  // 持续生成
  intervalId = setInterval(createSpark, 300);
});

onUnmounted(() => {
  if (intervalId) clearInterval(intervalId);
});
</script>

<style scoped lang="scss">
@use "./index.scss";

/* --- 左侧样式重构 --- */
.login-left {
  /* 强制覆盖原有的图片容器样式 */
  position: relative !important;
  display: flex !important;
  flex-direction: column !important;
  justify-content: center !important;
  align-items: center !important;
  /* 科技感深色渐变背景 */
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
  overflow: hidden !important;
  
  // 隐藏原来可能存在的 img
  .login-left-img {
    display: none; 
  }

  /* 粒子容器 */
  .particle-bg {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 1;
    pointer-events: none;
  }
}

/* --- 动态粒子样式 (使用 :deep 穿透 Scoped) --- */
:deep(.spark) {
  position: absolute;
  background: #FA4616; /* 爱马仕橙 */
  border-radius: 50%;
  opacity: 0;
  bottom: -20px;
  animation: float-up linear infinite;
}

@keyframes float-up {
  0% { transform: translateY(0) scale(0); opacity: 0; }
  20% { opacity: 0.8; }
  80% { opacity: 0.4; }
  100% { transform: translateY(-100vh) scale(1.5); opacity: 0; }
}

/* --- 装饰性代码文字 --- */
.code-decoration {
  position: absolute;
  font-family: 'Courier New', monospace;
  color: rgba(250, 70, 22, 0.08);
  font-size: 14px;
  user-select: none;
  z-index: 2;
  white-space: pre;
  line-height: 1.5;
  top: 10%;
  left: 10%;
  pointer-events: none;
}

/* --- 品牌内容区域 --- */
.left-content {
  position: relative;
  z-index: 10;
  text-align: center;
  padding: 40px;

  /* CSS绘制的动态Logo */
  .brand-logo-anim {
    position: relative;
    width: 100px;
    height: 100px;
    margin: 0 auto 30px;
    display: flex;
    align-items: center;
    justify-content: center;

    .circle-dashed {
      position: absolute;
      inset: 0;
      border: 2px dashed #475569;
      border-radius: 50%;
      animation: spin-slow 20s linear infinite;
    }

    .circle-solid {
      position: absolute;
      inset: 8px;
      border: 1px solid rgba(250, 70, 22, 0.3);
      border-radius: 50%;
    }

    .core-point {
      width: 40px;
      height: 40px;
      background: #FA4616;
      border-radius: 50%;
      box-shadow: 0 0 30px #FA4616;
      animation: pulse 2s infinite;
      z-index: 10;
    }

    .code-tag {
      position: absolute;
      bottom: -30px;
      font-family: monospace;
      color: #94a3b8;
      font-size: 12px;
      opacity: 0.6;
    }
  }

  .brand-title {
    font-size: 32px;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 15px;
    letter-spacing: 2px;
    text-shadow: 0 2px 10px rgba(0,0,0,0.3);
  }

  .brand-divider {
    width: 60px;
    height: 4px;
    background: #FA4616;
    margin: 0 auto 20px;
    border-radius: 2px;
    box-shadow: 0 0 10px rgba(250, 70, 22, 0.5);
  }

  .brand-slogan {
    font-size: 16px;
    color: #e2e8f0;
    font-weight: 300;
    letter-spacing: 4px;
    opacity: 0.9;
  }
}

/* 动画定义 */
@keyframes spin-slow {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(250, 70, 22, 0.4); }
  70% { box-shadow: 0 0 0 20px rgba(250, 70, 22, 0); }
  100% { box-shadow: 0 0 0 0 rgba(250, 70, 22, 0); }
}
</style>