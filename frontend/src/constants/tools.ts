/**
 * 工具包常量
 * 新增工具只需在此扩展，并添加对应路由与页面
 */
export interface ToolItem {
  id: string;
  name: string;
  description: string;
  icon: string;
  path: string;
}

export const TOOLS_LIST: ToolItem[] = [
  {
    id: "voice-clone",
    name: "声音复刻",
    description: "上传 5 秒以上音频，训练专属 AI 音色，支持文本转语音",
    icon: "Microphone",
    path: "/mp/tools/voice-clone"
  }
];
