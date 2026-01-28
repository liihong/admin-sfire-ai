import { gsap } from "gsap";

/**
 * 神经链接接入转场动画
 * 界面向中心坍缩 → 光束效果 → 炸开进入工作台
 */
export const neuralLinkTransition = (
  container: HTMLElement,
  onComplete?: () => void
): Promise<void> => {
  return new Promise(resolve => {
    const tl = gsap.timeline({
      onComplete: () => {
        if (onComplete) onComplete();
        resolve();
      }
    });

    // 阶段1: 向中心坍缩 (0-400ms)
    tl.to(container, {
      scale: 0.1,
      opacity: 0.3,
      duration: 0.4,
      ease: "power2.in"
    });

    // 阶段2: 光束效果 (400-600ms)
    tl.to(container, {
      scale: 0.05,
      opacity: 0.8,
      duration: 0.2,
      ease: "power2.inOut",
      boxShadow: "0 0 100px rgba(255, 107, 53, 0.8)"
    });

    // 阶段3: 炸开进入 (600-800ms)
    tl.to(container, {
      scale: 1,
      opacity: 1,
      duration: 0.2,
      ease: "power2.out",
      boxShadow: "0 0 0 rgba(255, 107, 53, 0)"
    });
  });
};

/**
 * 创建光束粒子效果
 */
export const createBeamParticles = (container: HTMLElement, count: number = 20) => {
  const particles: HTMLElement[] = [];

  for (let i = 0; i < count; i++) {
    const particle = document.createElement("div");
    particle.style.position = "absolute";
    particle.style.width = "2px";
    particle.style.height = "2px";
    particle.style.background = "#ff6b35";
    particle.style.borderRadius = "50%";
    particle.style.pointerEvents = "none";
    particle.style.opacity = "0";
    container.appendChild(particle);
    particles.push(particle);
  }

  // 动画粒子
  particles.forEach((particle, index) => {
    const angle = (Math.PI * 2 * index) / count;
    const distance = 200;
    const x = Math.cos(angle) * distance;
    const y = Math.sin(angle) * distance;

    gsap.fromTo(
      particle,
      {
        x: 0,
        y: 0,
        opacity: 1,
        scale: 1
      },
      {
        x: x,
        y: y,
        opacity: 0,
        scale: 0,
        duration: 0.8,
        delay: 0.4,
        ease: "power2.out"
      }
    );
  });

  // 清理粒子
  setTimeout(() => {
    particles.forEach(particle => {
      if (particle.parentNode) {
        particle.parentNode.removeChild(particle);
      }
    });
  }, 1200);
};































