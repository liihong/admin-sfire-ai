<template>
  <div class="mp-login-container flx-center">
    <div class="mp-login-box">
      <!-- 左侧品牌区域 -->
      <div class="login-left">
        <div class="left-content">
          <div class="brand-logo">
            <img class="logo-img" src="@/assets/images/logo.svg" alt="logo" />
          </div>
          <h1 class="brand-title">SFire AI</h1>
          <div class="brand-divider"></div>
          <p class="brand-slogan">智能创作 · 无限可能</p>
        </div>
      </div>

      <!-- 右侧登录表单 -->
      <div class="login-form">
        <div class="login-header">
          <img class="login-icon" src="@/assets/images/logo.svg" alt="" />
          <h2 class="logo-text">小程序用户登录</h2>
        </div>

        <!-- 微信扫码登录 -->
        <div v-if="loginMode === 'qrcode'" class="qrcode-login">
          <div class="qrcode-container">
            <div v-if="qrcodeLoading" class="qrcode-loading">
              <el-icon class="is-loading"><Loading /></el-icon>
              <p>正在生成二维码...</p>
            </div>
            <div v-else-if="qrcodeError" class="qrcode-error">
              <el-icon><Warning /></el-icon>
              <p>{{ qrcodeError }}</p>
              <el-button type="primary" @click="generateQrcode">重新生成</el-button>
            </div>
            <div v-else class="qrcode-wrapper">
              <img v-if="qrcodeImageUrl" :src="qrcodeImageUrl" alt="小程序码" class="qrcode-image" @load="handleImageLoad" @error="handleImageError" />
              <div v-else ref="qrcodeRef" class="qrcode"></div>
              <p class="qrcode-tip">使用微信扫码登录</p>
            </div>
          </div>
          <div class="login-tips">
            <el-link type="primary" @click="switchLoginMode('account')">使用账号密码登录</el-link>
          </div>
        </div>

        <!-- 账号密码登录 -->
        <div v-else class="account-login">
          <el-form ref="loginFormRef" :model="loginForm" :rules="loginRules" size="large">
            <el-form-item prop="username">
              <el-input v-model="loginForm.username" placeholder="请输入手机号">
                <template #prefix>
                  <el-icon class="el-input__icon"><User /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
                show-password
                autocomplete="new-password"
                @keyup.enter="handleAccountLogin"
              >
                <template #prefix>
                  <el-icon class="el-input__icon"><Lock /></el-icon>
                </template>
              </el-input>
            </el-form-item>
          </el-form>
          <div class="login-btn">
            <el-button round size="large" @click="switchLoginMode('qrcode')">返回扫码登录</el-button>
            <el-button round size="large" type="primary" :loading="loading" @click="handleAccountLogin">
              登录
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts" name="MPLogin">
import { ref, reactive, onMounted, onBeforeUnmount } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElForm } from "element-plus";
import { User, Lock, Loading, Warning } from "@element-plus/icons-vue";
import { useMPUserStore } from "@/stores/modules/miniprogramUser";
import { MP_HOME_URL } from "@/config";
import { generateQrcodeApi, checkQrcodeStatusApi } from "@/api/modules/miniprogram";

const router = useRouter();
const mpUserStore = useMPUserStore();

type LoginMode = "qrcode" | "account";
const loginMode = ref<LoginMode>("qrcode");

const loginFormRef = ref<InstanceType<typeof ElForm>>();
const loading = ref(false);
const loginForm = reactive({
  username: "",
  password: ""
});

const loginRules = reactive({
  username: [
    { required: true, message: "请输入手机号", trigger: "blur" },
    { pattern: /^1[3-9]\d{9}$/, message: "请输入正确的手机号", trigger: "blur" }
  ],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }]
});

// 小程序码相关
const qrcodeRef = ref<HTMLElement>();
const qrcodeLoading = ref(false);
const qrcodeError = ref("");
const qrcodeImageUrl = ref("");
const sceneStr = ref("");
let qrcodeCheckInterval: any = null;

// 图片加载成功处理
const handleImageLoad = () => {
  // 图片加载成功，无需特殊处理
};

// 图片加载失败处理
const handleImageError = () => {
  console.error("小程序码图片加载失败");
};

// 切换登录方式
const switchLoginMode = (mode: LoginMode) => {
  loginMode.value = mode;
  if (mode === "qrcode") {
    generateQrcode();
  }
};

// 生成小程序码
const generateQrcode = async () => {
  qrcodeLoading.value = true;
  qrcodeError.value = "";
  qrcodeImageUrl.value = "";

  try {
    // 调用后端接口生成小程序码
    const { data } = await generateQrcodeApi();
    
    if (data?.qrcode_url && data?.scene_str) {
      qrcodeImageUrl.value = data.qrcode_url;
      sceneStr.value = data.scene_str;
      qrcodeLoading.value = false;
      
      // 开始轮询检查登录状态
      startQrcodeCheck();
    } else {
      throw new Error("生成小程序码失败：未获取到数据");
    }
  } catch (error: any) {
    console.error("生成小程序码失败:", error);
    qrcodeLoading.value = false;
    qrcodeError.value = error?.msg || "生成小程序码失败，请重试";
  }
};

// 开始轮询检查登录状态
const startQrcodeCheck = () => {
  // 清除之前的定时器
  if (qrcodeCheckInterval) {
    clearInterval(qrcodeCheckInterval);
  }

  if (!sceneStr.value) {
    console.error("scene_str 不存在，无法开始轮询");
    return;
  }

  // 每2秒轮询检查登录状态
  qrcodeCheckInterval = setInterval(async () => {
    try {
      const { data } = await checkQrcodeStatusApi(sceneStr.value);
      
      if (data?.status === "authorized") {
        // 用户已授权，完成登录
        clearInterval(qrcodeCheckInterval);
        qrcodeCheckInterval = null;
        
        if (data.token && data.userInfo) {
          // 保存token和用户信息
          mpUserStore.setToken(data.token);
          mpUserStore.setUserInfo(data.userInfo);
          
          ElMessage.success("登录成功");
          router.push(MP_HOME_URL);
        } else {
          ElMessage.error("登录失败：未获取到token");
        }
      } else if (data?.status === "expired") {
        // 已过期，停止轮询
        clearInterval(qrcodeCheckInterval);
        qrcodeCheckInterval = null;
        qrcodeError.value = "登录已过期，请重新生成小程序码";
      }
      // status === "waiting" 时继续等待
    } catch (error: any) {
      console.error("检查登录状态失败:", error);
      // 不显示错误，继续轮询
    }
  }, 2000);
};

// 微信登录
const handleWechatLogin = async (code: string, phoneCode?: string) => {
  loading.value = true;
  try {
    const success = await mpUserStore.wechatLogin({
      code,
      phone_code: phoneCode
    });

    if (success) {
      ElMessage.success("登录成功");
      router.push(MP_HOME_URL);
    }
  } catch (error: any) {
    ElMessage.error(error?.msg || "登录失败，请稍后重试");
  } finally {
    loading.value = false;
  }
};

// 账号密码登录
const handleAccountLogin = async () => {
  if (!loginFormRef.value) return;

  await loginFormRef.value.validate(async valid => {
    if (!valid) return;

    loading.value = true;
    try {
      const success = await mpUserStore.accountLogin({
        phone: loginForm.username, // 使用username字段输入手机号
        password: loginForm.password
      });
      
      if (success) {
        ElMessage.success("登录成功");
        router.push(MP_HOME_URL);
      }
    } catch (error: any) {
      ElMessage.error(error?.msg || "登录失败，请稍后重试");
    } finally {
      loading.value = false;
    }
  });
};

onMounted(() => {
  // 如果已登录，跳转到首页
  if (mpUserStore.isLogin) {
    router.push(MP_HOME_URL);
    return;
  }

  // 默认生成二维码
  if (loginMode.value === "qrcode") {
    generateQrcode();
  }
});

onBeforeUnmount(() => {
  // 清除定时器
  if (qrcodeCheckInterval) {
    clearInterval(qrcodeCheckInterval);
  }
});
</script>

<style scoped lang="scss">
// 爱马仕橙主题色
$hermes-orange: #ff7700;
$hermes-orange-light: #ff9a3c;
$hermes-orange-dark: #e85d00;
$hermes-orange-gradient: linear-gradient(135deg, #ff7700 0%, #ff9a3c 50%, #ff7700 100%);
$hermes-orange-bg: linear-gradient(135deg, #fff5eb 0%, #ffe4cc 50%, #ffd4a3 100%);

.mp-login-container {
  height: 100vh;
  min-height: 600px;
  position: relative;
  background: linear-gradient(135deg, #602d00 0%, #ff9a3c 50%, #311400 100%);
  overflow: hidden;

  // 添加动态背景装饰
  &::before {
    content: "";
    position: absolute;
    top: -50%;
    right: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
    animation: rotate 20s linear infinite;
  }

  &::after {
    content: "";
    position: absolute;
    bottom: -30%;
    left: -30%;
    width: 150%;
    height: 150%;
    background: radial-gradient(circle, rgba(255, 154, 60, 0.15) 0%, transparent 70%);
    animation: rotate 25s linear infinite reverse;
  }

  @keyframes rotate {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }

  .mp-login-box {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 90%;
    max-width: 1100px;
    height: 650px;
    background: rgba(255, 255, 255, 0.98);
    backdrop-filter: blur(20px);
    border-radius: 24px;
    box-shadow: 
      0 25px 80px rgba(255, 119, 0, 0.25),
      0 10px 30px rgba(0, 0, 0, 0.1),
      inset 0 1px 0 rgba(255, 255, 255, 0.6);
    overflow: hidden;
    position: relative;
    z-index: 1;
    transition: all 0.3s ease;

    &:hover {
      box-shadow: 
        0 30px 100px rgba(255, 119, 0, 0.3),
        0 15px 40px rgba(0, 0, 0, 0.15),
        inset 0 1px 0 rgba(255, 255, 255, 0.6);
      transform: translateY(-2px);
    }

    .login-left {
      flex: 1;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 50%, #1a1a1a 100%);
      color: white;
      position: relative;
      overflow: hidden;

      // 添加装饰性光效
      &::before {
        content: "";
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255, 119, 0, 0.1) 0%, transparent 70%);
        animation: pulse 4s ease-in-out infinite;
      }

      @keyframes pulse {
        0%, 100% {
          opacity: 0.3;
          transform: scale(1);
        }
        50% {
          opacity: 0.6;
          transform: scale(1.1);
        }
      }

      .left-content {
        text-align: center;
        padding: 50px 40px;
        position: relative;
        z-index: 1;
        animation: fadeInUp 0.8s ease-out;

        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .brand-logo {
          margin-bottom: 35px;
          position: relative;

          .logo-img {
            width: 100px;
            height: 100px;
            filter: drop-shadow(0 10px 20px rgba(255, 119, 0, 0.3));
            transition: all 0.3s ease;
            animation: logoFloat 3s ease-in-out infinite;

            @keyframes logoFloat {
              0%, 100% {
                    transform: translateY(0);
                  }
              50% {
                    transform: translateY(-10px);
                  }
            }

            &:hover {
              transform: scale(1.1) translateY(-5px);
              filter: drop-shadow(0 15px 30px rgba(255, 119, 0, 0.5));
            }
          }
        }

        .brand-title {
          font-size: 42px;
          font-weight: 900;
          margin-bottom: 20px;
          letter-spacing: 3px;
          background: linear-gradient(135deg, #ffffff 0%, #ffd4a3 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          text-shadow: 0 2px 10px rgba(255, 119, 0, 0.3);
        }

        .brand-divider {
          width: 80px;
          height: 5px;
          background: $hermes-orange-gradient;
          margin: 0 auto 25px;
          border-radius: 3px;
          box-shadow: 0 4px 15px rgba(255, 119, 0, 0.4);
          position: relative;

          &::after {
            content: "";
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 100%;
            height: 100%;
            background: $hermes-orange-gradient;
            filter: blur(8px);
            opacity: 0.6;
            z-index: -1;
          }
        }

        .brand-slogan {
          font-size: 18px;
          color: rgba(255, 255, 255, 0.85);
          font-weight: 300;
          letter-spacing: 5px;
          text-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        }
      }
    }

    .login-form {
      flex: 1;
      padding: 70px 60px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      background: linear-gradient(to bottom, rgba(255, 255, 255, 0.95), rgba(255, 250, 240, 0.95));

      .login-header {
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 50px;
        animation: fadeInDown 0.8s ease-out;

        @keyframes fadeInDown {
          from {
            opacity: 0;
            transform: translateY(-20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .login-icon {
          width: 56px;
          height: 56px;
          margin-right: 18px;
          filter: drop-shadow(0 4px 8px rgba(255, 119, 0, 0.2));
          transition: all 0.3s ease;

          &:hover {
            transform: scale(1.1) rotate(5deg);
          }
        }

        .logo-text {
          font-size: 28px;
          font-weight: 700;
          background: linear-gradient(135deg, #333 0%, #666 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          margin: 0;
          letter-spacing: 1px;
        }
      }

      .qrcode-login {
        animation: fadeIn 0.8s ease-out;

        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }

        .qrcode-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-height: 320px;

          .qrcode-loading,
          .qrcode-error {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 24px;
            color: var(--el-text-color-regular);

            .el-icon {
              font-size: 56px;
              color: $hermes-orange;
            }

            p {
              font-size: 16px;
              color: var(--el-text-color-regular);
            }
          }

            .qrcode-wrapper {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 24px;

            .qrcode,
            .qrcode-image {
              width: 280px;
              height: 280px;
              padding: 24px;
              background: white;
              border-radius: 16px;
              box-shadow: 
                0 8px 24px rgba(255, 119, 0, 0.15),
                0 2px 8px rgba(0, 0, 0, 0.08),
                inset 0 1px 0 rgba(255, 255, 255, 0.9);
              border: 2px solid rgba(255, 119, 0, 0.1);
              transition: all 0.3s ease;
              object-fit: contain;

              &:hover {
                transform: translateY(-4px);
                box-shadow: 
                  0 12px 32px rgba(255, 119, 0, 0.2),
                  0 4px 12px rgba(0, 0, 0, 0.1),
                  inset 0 1px 0 rgba(255, 255, 255, 0.9);
              }
            }

            .qrcode-tip {
              color: var(--el-text-color-regular);
              font-size: 15px;
              font-weight: 500;
              letter-spacing: 0.5px;
            }
          }
        }

        .login-tips {
          text-align: center;
          margin-top: 35px;

          :deep(.el-link) {
            font-size: 15px;
            font-weight: 500;
            color: $hermes-orange;
            transition: all 0.3s ease;

            &:hover {
              color: $hermes-orange-dark;
              transform: translateX(2px);
            }
          }
        }
      }

      .account-login {
        animation: fadeIn 0.8s ease-out;

        :deep(.el-form-item) {
          margin-bottom: 32px;

          .el-input__wrapper {
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
            transition: all 0.3s ease;
            background: rgba(255, 255, 255, 0.9);

            &:hover {
              box-shadow: 0 4px 12px rgba(255, 119, 0, 0.15);
            }

            &.is-focus {
              box-shadow: 0 4px 16px rgba(255, 119, 0, 0.25);
            }
          }

          .el-input__prefix {
            .el-icon {
              color: $hermes-orange;
            }
          }
        }

        .login-btn {
          display: flex;
          justify-content: space-between;
          gap: 18px;
          margin-top: 35px;

          :deep(.el-button) {
            flex: 1;
            height: 48px;
            font-size: 16px;
            font-weight: 600;
            border-radius: 12px;
            transition: all 0.3s ease;
            letter-spacing: 0.5px;

            &.el-button--default {
              background: rgba(255, 255, 255, 0.9);
              border: 2px solid rgba(255, 119, 0, 0.2);
              color: var(--el-text-color-regular);

              &:hover {
                background: rgba(255, 119, 0, 0.05);
                border-color: $hermes-orange;
                color: $hermes-orange;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(255, 119, 0, 0.2);
              }
            }

            &.el-button--primary {
              background: $hermes-orange-gradient;
              border: none;
              box-shadow: 0 4px 16px rgba(255, 119, 0, 0.3);

              &:hover {
                background: linear-gradient(135deg, #ff9a3c 0%, #ff7700 50%, #e85d00 100%);
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(255, 119, 0, 0.4);
              }

              &:active {
                transform: translateY(0);
                box-shadow: 0 2px 8px rgba(255, 119, 0, 0.3);
              }
            }
          }
        }
      }
    }
  }
}

@media screen and (max-width: 900px) {
  .mp-login-container {
    &::before,
    &::after {
      display: none;
    }

    .mp-login-box {
      flex-direction: column;
      height: auto;
      min-height: 600px;
      max-width: 95%;
      border-radius: 20px;

      .login-left {
        display: none;
      }

      .login-form {
        width: 100%;
        padding: 50px 35px;
        background: rgba(255, 255, 255, 0.98);
      }
    }
  }
}
</style>

