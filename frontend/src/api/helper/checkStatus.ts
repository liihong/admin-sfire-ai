import { ElMessage, ElMessageBox } from "element-plus";
import router from "@/routers";

/**
 * @description: 校验网络请求状态码
 * @param {Number} status
 * @param {String} message 后端返回的错误消息（可选）
 * @return void
 */
export const checkStatus = (status: number, message?: string) => {
  switch (status) {
    case 400:
      ElMessage.error(message || "请求失败！请您稍后重试");
      break;
    case 401:
      ElMessage.error("登录失效！请您重新登录");
      break;
    case 402:
      // 算力不足 - AI 业务专用
      handleInsufficientBalance(message);
      break;
    case 403:
      ElMessage.error("当前账号无权限访问！");
      break;
    case 404:
      ElMessage.error("你所访问的资源不存在！");
      break;
    case 405:
      ElMessage.error("请求方式错误！请您稍后重试");
      break;
    case 408:
      ElMessage.error("请求超时！请您稍后重试");
      break;
    case 409:
      // 业务冲突（如：重复操作）
      ElMessage.warning(message || "操作冲突，请刷新后重试");
      break;
    case 423:
      // 账户被锁定/封禁
      ElMessage.error(message || "您的账户已被锁定，请联系客服");
      break;
    case 429:
      // 请求过于频繁
      ElMessage.warning("操作过于频繁，请稍后再试");
      break;
    // 5XX 服务器错误统一处理
    case 500:
    case 501:
    case 502:
    case 503:
    case 504:
    case 505:
    case 506:
    case 507:
    case 508:
    case 510:
    case 511:
      // 所有5XX错误统一提示：系统服务器异常，请稍后尝试，或联系客服
      ElMessage.error("系统服务器异常，请稍后尝试，或联系客服");
      break;
    default:
      // 其他未处理的5XX错误也统一提示
      if (status >= 500 && status < 600) {
        ElMessage.error("系统服务器异常，请稍后尝试，或联系客服");
      } else {
        ElMessage.error(message || "请求失败！");
      }
  }
};

/**
 * @description: 处理算力不足的情况
 * @param {String} message 错误消息
 */
const handleInsufficientBalance = (message?: string) => {
  ElMessageBox.confirm(message || "您的算力不足，是否前往充值？", "算力不足", {
    confirmButtonText: "立即充值",
    cancelButtonText: "稍后再说",
    type: "warning"
  })
    .then(() => {
      // 跳转到充值页面
      router.push("/compute/recharge");
    })
    .catch(() => {
      // 用户取消
    });
};

/**
 * @description: AI 业务错误码映射
 */
export const AI_ERROR_CODES = {
  INSUFFICIENT_BALANCE: 402, // 算力不足
  MODEL_UNAVAILABLE: 4001, // 模型不可用
  CONTEXT_TOO_LONG: 4002, // 上下文过长
  RATE_LIMIT_EXCEEDED: 4003, // 超出速率限制
  CONTENT_FILTERED: 4004, // 内容被过滤
  STREAM_INTERRUPTED: 4005 // 流式传输中断
} as const;

/**
 * @description: 处理 AI 业务特定错误
 * @param {Number} code 错误码
 * @param {String} message 错误消息
 */
export const handleAIError = (code: number, message?: string) => {
  switch (code) {
    case AI_ERROR_CODES.INSUFFICIENT_BALANCE:
      handleInsufficientBalance(message);
      break;
    case AI_ERROR_CODES.MODEL_UNAVAILABLE:
      ElMessage.error(message || "当前模型暂不可用，请选择其他模型");
      break;
    case AI_ERROR_CODES.CONTEXT_TOO_LONG:
      ElMessage.warning(message || "对话内容过长，请清理历史消息");
      break;
    case AI_ERROR_CODES.RATE_LIMIT_EXCEEDED:
      ElMessage.warning(message || "请求过于频繁，请稍后再试");
      break;
    case AI_ERROR_CODES.CONTENT_FILTERED:
      ElMessage.warning(message || "内容包含敏感信息，请修改后重试");
      break;
    case AI_ERROR_CODES.STREAM_INTERRUPTED:
      ElMessage.error(message || "连接中断，请重试");
      break;
    default:
      ElMessage.error(message || "AI 服务异常，请稍后重试");
  }
};
