import http from "@/api";
import { PORT1 } from "@/api/config/servicePort";

/**
 * 工具包 API
 * C 端 /v1/client/tools ；管理端 /v1/admin/tools
 */

const MP_API_PREFIX = "/v1/client";
const ADMIN_TOOLS = PORT1 + "/tools/voice-clone";
const ADMIN_DOUYIN_CAPTION = PORT1 + "/tools/douyin-caption";

// ============== 声音复刻 ==============

export interface VoiceTrainStatus {
  has_speaker: boolean;
  speaker_id: string | null;
  status: string;
  train_version?: number;
}

export interface VoiceUploadResponse {
  speaker_id: string;
  status: string;
  train_version: number;
}

export interface SynthesizeResponse {
  audio_base64: string;
  format: string;
}

/** 上传训练音频 */
export const uploadVoiceAudioApi = (file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  return http.post<{ code: number; data: VoiceUploadResponse; msg: string }>(
    MP_API_PREFIX + "/tools/voice-clone/upload",
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" },
      loading: true
    }
  );
};

/** 查询训练状态 */
export const getVoiceTrainStatusApi = () => {
  return http.get<{ code: number; data: VoiceTrainStatus; msg: string }>(
    MP_API_PREFIX + "/tools/voice-clone/status",
    {},
    { loading: false }
  );
};

/** 文本转语音 */
export const synthesizeVoiceApi = (params: { text: string; speaker_id?: string }) => {
  return http.post<{ code: number; data: SynthesizeResponse; msg: string }>(
    MP_API_PREFIX + "/tools/voice-clone/synthesize",
    params,
    { loading: true }
  );
};

/** 管理端：声音复刻（同路径，走 admin 鉴权） */
export const adminUploadVoiceAudioApi = (file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  return http.post<{ code: number; data: VoiceUploadResponse; msg: string }>(
    ADMIN_TOOLS + "/upload",
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" },
      loading: true
    }
  );
};

export const adminGetVoiceTrainStatusApi = () => {
  return http.get<{ code: number; data: VoiceTrainStatus; msg: string }>(
    ADMIN_TOOLS + "/status",
    {},
    { loading: false }
  );
};

export const adminSynthesizeVoiceApi = (params: { text: string; speaker_id?: string }) => {
  return http.post<{ code: number; data: SynthesizeResponse; msg: string }>(
    ADMIN_TOOLS + "/synthesize",
    params,
    { loading: true }
  );
};

// ============== 抖音文案提取 ==============

export interface DouyinCaptionExtractData {
  text: string;
  aweme_id: string;
  title?: string | null;
  /** C 端成功时返回；管理端自测不扣费，通常无此字段 */
  coin_cost?: number;
}

/** C 端：从抖音链接提取口播文案 */
export const extractDouyinCaptionApi = (params: { url: string }) => {
  return http.post<{ code: number; data: DouyinCaptionExtractData; msg: string }>(
    MP_API_PREFIX + "/tools/douyin-caption/extract",
    params,
    { loading: true }
  );
};

/** 管理端：抖音文案提取 */
export const adminExtractDouyinCaptionApi = (params: { url: string }) => {
  return http.post<{ code: number; data: DouyinCaptionExtractData; msg: string }>(
    ADMIN_DOUYIN_CAPTION + "/extract",
    params,
    { loading: true }
  );
};
