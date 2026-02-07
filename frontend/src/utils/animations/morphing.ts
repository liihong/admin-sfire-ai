import { gsap } from "gsap";

/**
 * Morphing 变形动画
 * 用于智能体切换时的界面变形效果
 */
export const morphingTransition = (
  fromElement: HTMLElement,
  toElement: HTMLElement,
  duration: number = 0.4
): Promise<void> => {
  return new Promise(resolve => {
    const tl = gsap.timeline({
      onComplete: () => resolve()
    });

    // 获取元素位置和尺寸
    const fromRect = fromElement.getBoundingClientRect();
    const toRect = toElement.getBoundingClientRect();

    // 创建临时覆盖层
    const overlay = document.createElement("div");
    overlay.style.position = "fixed";
    overlay.style.top = `${fromRect.top}px`;
    overlay.style.left = `${fromRect.left}px`;
    overlay.style.width = `${fromRect.width}px`;
    overlay.style.height = `${fromRect.height}px`;
    overlay.style.background = "var(--ip-os-bg-secondary)";
    overlay.style.borderRadius = "8px";
    overlay.style.zIndex = "9999";
    overlay.style.opacity = "0";
    document.body.appendChild(overlay);

    // 阶段1: 淡出原元素
    tl.to(fromElement, {
      opacity: 0,
      duration: duration * 0.3,
      ease: "power2.in"
    });

    // 阶段2: 变形覆盖层
    tl.to(overlay, {
      opacity: 1,
      x: toRect.left - fromRect.left,
      y: toRect.top - fromRect.top,
      width: toRect.width,
      height: toRect.height,
      duration: duration * 0.4,
      ease: "power2.inOut"
    });

    // 阶段3: 显示新元素并移除覆盖层
    tl.to(toElement, {
      opacity: 1,
      duration: duration * 0.3,
      ease: "power2.out"
    });

    tl.to(overlay, {
      opacity: 0,
      duration: duration * 0.1,
      onComplete: () => {
        document.body.removeChild(overlay);
      }
    });
  });
};

/**
 * 简单的淡入淡出切换
 */
export const fadeTransition = (
  fromElement: HTMLElement | null,
  toElement: HTMLElement,
  duration: number = 0.4
): Promise<void> => {
  return new Promise(resolve => {
    const tl = gsap.timeline({
      onComplete: () => resolve()
    });

    if (fromElement) {
      tl.to(fromElement, {
        opacity: 0,
        duration: duration * 0.5,
        ease: "power2.in"
      });
    }

    gsap.set(toElement, { opacity: 0 });
    tl.to(toElement, {
      opacity: 1,
      duration: duration * 0.5,
      ease: "power2.out"
    });
  });
};












































