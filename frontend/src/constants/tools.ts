/**
 * 工具包说明（展示用）
 * 实际列表数据来自后端 tool_packages + 前端 toolRegistry 注册页面组件
 * @see src/config/toolRegistry.ts
 * @see src/api/modules/toolPackage.ts
 */
export interface ToolItem {
  id: string;
  name: string;
  description: string;
  icon: string;
  path: string;
}

/** 仅作类型/文档参考；运行时请以接口与 registry 为准 */
export const TOOLS_LIST: ToolItem[] = [
  {
    id: "voice-clone",
    name: "声音复刻",
    description: "上传 5 秒以上音频，训练专属 AI 音色，支持文本转语音",
    icon: "Microphone",
    path: "/mp/tools/voice-clone"
  }
];
