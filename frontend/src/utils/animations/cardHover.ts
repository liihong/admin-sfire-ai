import { gsap } from "gsap";

/**
 * 卡片悬停动画
 * 缩放 + 光晕效果
 */
export const cardHoverAnimation = (card: HTMLElement) => {
  const glow = card.querySelector(".ip-card-glow") as HTMLElement;
  
  if (!glow) {
    // 创建光晕元素
    const glowElement = document.createElement("div");
    glowElement.className = "ip-card-glow";
    glowElement.style.position = "absolute";
    glowElement.style.top = "0";
    glowElement.style.left = "0";
    glowElement.style.width = "100%";
    glowElement.style.height = "100%";
    glowElement.style.borderRadius = "inherit";
    glowElement.style.pointerEvents = "none";
    glowElement.style.opacity = "0";
    glowElement.style.boxShadow = "0 0 30px rgba(255, 107, 53, 0.5)";
    card.style.position = "relative";
    card.appendChild(glowElement);
  }

  gsap.to(card, {
    scale: 1.05,
    duration: 0.3,
    ease: "power2.out"
  });

  gsap.to(card.querySelector(".ip-card-glow"), {
    opacity: 1,
    duration: 0.3,
    ease: "power2.out"
  });
};

/**
 * 卡片离开动画
 */
export const cardLeaveAnimation = (card: HTMLElement) => {
  gsap.to(card, {
    scale: 1,
    duration: 0.3,
    ease: "power2.out"
  });

  gsap.to(card.querySelector(".ip-card-glow"), {
    opacity: 0,
    duration: 0.3,
    ease: "power2.out"
  });
};



































