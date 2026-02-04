<template>
  <span class="count-up">{{ displayValue }}</span>
</template>

<script setup lang="ts" name="CountUp">
import { ref, watch, onMounted } from "vue";

interface Props {
  endVal: number;
  startVal?: number;
  duration?: number;
  decimals?: number;
  separator?: string;
  prefix?: string;
  suffix?: string;
}

const props = withDefaults(defineProps<Props>(), {
  startVal: 0,
  duration: 2,
  decimals: 0,
  separator: ",",
  prefix: "",
  suffix: ""
});

const displayValue = ref("");
let animationFrame: number | null = null;

// 格式化数字
const formatNumber = (num: number): string => {
  const fixedNum = num.toFixed(props.decimals);
  const parts = fixedNum.split(".");
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, props.separator);
  return props.prefix + parts.join(".") + props.suffix;
};

// 缓动函数
const easeOutQuart = (t: number): number => {
  return 1 - Math.pow(1 - t, 4);
};

// 执行动画
const startAnimation = () => {
  if (animationFrame) {
    cancelAnimationFrame(animationFrame);
  }

  const startTime = performance.now();
  const startVal = props.startVal;
  const endVal = props.endVal;
  const duration = props.duration * 1000;

  const animate = (currentTime: number) => {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const easedProgress = easeOutQuart(progress);
    const currentVal = startVal + (endVal - startVal) * easedProgress;

    displayValue.value = formatNumber(currentVal);

    if (progress < 1) {
      animationFrame = requestAnimationFrame(animate);
    }
  };

  animationFrame = requestAnimationFrame(animate);
};

// 监听值变化
watch(
  () => props.endVal,
  () => {
    startAnimation();
  }
);

onMounted(() => {
  startAnimation();
});
</script>

<style scoped lang="scss">
.count-up {
  font-variant-numeric: tabular-nums;
}
</style>








































