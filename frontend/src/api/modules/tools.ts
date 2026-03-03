import http from "@/api";

/**
 * 工具包 API
 * C 端对接 /api/v1/client/tools
 */

const MP_API_PREFIX = "/v1/client";

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
