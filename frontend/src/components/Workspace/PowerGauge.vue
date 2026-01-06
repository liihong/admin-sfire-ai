<template>
  <div class="power-gauge">
    <div class="power-gauge-header">
      <span class="power-gauge-label">算力余额</span>
      <span class="power-gauge-value">{{ formatPower(power) }}</span>
    </div>
    <div class="ip-os-power-gauge" :style="{ '--power-percent': powerPercent + '%' }">
      <div class="power-gauge-fill" :style="{ width: powerPercent + '%' }"></div>
    </div>
    <div class="power-gauge-footer">
      <span class="power-gauge-warning" v-if="powerPercent < 20">
        <el-icon><Warning /></el-icon>
        算力不足，请及时充值
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Warning } from "@element-plus/icons-vue";

interface Props {
  power: number;
  maxPower?: number;
}

const props = withDefaults(defineProps<Props>(), {
  maxPower: 10000
});

const powerPercent = computed(() => {
  return Math.min((props.power / props.maxPower) * 100, 100);
});

const formatPower = (power: number) => {
  if (power >= 10000) {
    return (power / 10000).toFixed(1) + "万";
  }
  return power.toLocaleString();
};
</script>

<style scoped lang="scss">
@use "@/styles/ip-os-theme.scss" as *;

.power-gauge {
  padding: 16px;
  background: var(--ip-os-bg-secondary);
  border-radius: 8px;
  border: 1px solid var(--ip-os-border-primary);
}

.power-gauge-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  
  .power-gauge-label {
    font-size: 14px;
    color: var(--ip-os-text-secondary);
  }
  
  .power-gauge-value {
    font-size: 20px;
    font-weight: 700;
    color: var(--ip-os-accent-primary);
    font-family: "DIN", monospace;
  }
}

.ip-os-power-gauge {
  position: relative;
  width: 100%;
  height: 8px;
  background: var(--ip-os-bg-tertiary);
  border-radius: 4px;
  overflow: hidden;
  
  .power-gauge-fill {
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    background: linear-gradient(90deg, var(--ip-os-accent-primary), var(--ip-os-accent-secondary));
    border-radius: 4px;
    transition: width 0.3s ease;
    box-shadow: 0 0 10px var(--ip-os-accent-glow);
    
    &::after {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
      animation: shimmer 2s infinite;
    }
  }
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

.power-gauge-footer {
  margin-top: 8px;
  
  .power-gauge-warning {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    color: var(--ip-os-accent-primary);
    
    .el-icon {
      font-size: 14px;
    }
  }
}
</style>

