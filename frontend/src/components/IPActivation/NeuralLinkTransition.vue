<template>
  <Transition name="neural-link">
    <div v-if="visible" class="neural-link-transition" ref="transitionRef">
      <div class="neural-link-beam"></div>
      <div class="neural-link-message">{{ message }}</div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from "vue";
import { neuralLinkTransition, createBeamParticles } from "@/utils/animations/neuralLink";

interface Props {
  visible: boolean;
  message?: string;
}

interface Emits {
  (e: "complete"): void;
}

const props = withDefaults(defineProps<Props>(), {
  message: "神经链接接入中..."
});

const emit = defineEmits<Emits>();

const transitionRef = ref<HTMLElement>();

watch(
  () => props.visible,
  async newVal => {
    if (newVal) {
      // 等待 DOM 更新
      await nextTick();
      
      if (transitionRef.value) {
        // 创建粒子效果
        createBeamParticles(transitionRef.value);
        
        // 执行转场动画
        await neuralLinkTransition(transitionRef.value);
        
        // 通知父组件动画完成
        emit("complete");
      }
    }
  }
);
</script>

<style scoped lang="scss">
.neural-link-transition {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: var(--ip-os-bg-primary);
  z-index: 10000;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.neural-link-beam {
  width: 200px;
  height: 200px;
  border-radius: 50%;
  background: radial-gradient(circle, var(--ip-os-accent-primary), transparent);
  animation: beamPulse 1s ease-in-out infinite;
  box-shadow: 0 0 100px var(--ip-os-accent-primary);
}

.neural-link-message {
  margin-top: 40px;
  font-size: 18px;
  color: var(--ip-os-accent-primary);
  text-align: center;
  animation: messageFade 1.5s ease-in-out infinite;
}

@keyframes beamPulse {
  0%, 100% {
    transform: scale(1);
    opacity: 0.8;
  }
  50% {
    transform: scale(1.2);
    opacity: 1;
  }
}

@keyframes messageFade {
  0%, 100% {
    opacity: 0.6;
  }
  50% {
    opacity: 1;
  }
}

.neural-link-enter-active,
.neural-link-leave-active {
  transition: opacity 0.3s ease;
}

.neural-link-enter-from,
.neural-link-leave-to {
  opacity: 0;
}
</style>

