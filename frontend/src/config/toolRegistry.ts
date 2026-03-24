/**
 * 工具页面注册表：code -> 页面组件
 * 新增工具：在此注册 + 后端写入 tool_packages + 实现 services/tools 与路由
 */
import type { Component } from "vue";
import { markRaw } from "vue";
import VoiceClone from "@/views/tools/voice-clone/index.vue";
import DouyinCaption from "@/views/tools/douyin-caption/index.vue";

export const toolPageRegistry: Record<string, Component> = {
  "voice-clone": markRaw(VoiceClone),
  "douyin-caption": markRaw(DouyinCaption)
};

export function resolveToolPage(code: string): Component | null {
  return toolPageRegistry[code] ?? null;
}
