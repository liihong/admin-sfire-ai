<template>
  <div class="mp-user">
    <el-row :gutter="20">
      <!-- 用户信息卡片 -->
      <el-col :xs="24" :sm="24" :md="8">
        <el-card class="user-info-card">
          <div class="user-avatar-section">
            <el-upload
              class="avatar-uploader"
              :show-file-list="false"
              :before-upload="beforeAvatarUpload"
              :http-request="handleAvatarUpload"
            >
              <el-avatar :src="userDetail?.avatar || userInfo.avatarUrl" :size="100">
                <el-icon><UserFilled /></el-icon>
              </el-avatar>
              <div class="avatar-mask">
                <el-icon><Camera /></el-icon>
                <span>更换头像</span>
              </div>
            </el-upload>
            <h3 class="user-name">{{ userDetail?.nickname || userInfo.nickname || "用户" }}</h3>
            <p class="user-status">{{ userDetail?.partnerStatus || "普通用户" }}</p>
          </div>
          <el-divider />
          <div class="user-stats">
            <div class="stat-item">
              <span class="stat-label">算力余额</span>
              <span class="stat-value">{{ userDetail?.power || "0" }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">合伙人资产</span>
              <span class="stat-value">¥{{ userDetail?.partnerBalance || "0.00" }}</span>
            </div>
            <div v-if="userDetail?.expireDate" class="stat-item">
              <span class="stat-label">会员到期</span>
              <span class="stat-value">{{ userDetail.expireDate }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 用户信息编辑 -->
      <el-col :xs="24" :sm="24" :md="16">
        <el-card>
          <template #header>
            <span>个人信息</span>
          </template>
          <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
            <el-form-item label="昵称" prop="nickname">
              <el-input v-model="formData.nickname" placeholder="请输入昵称" />
            </el-form-item>
            <el-form-item label="手机号">
              <div v-if="userDetail">
                <el-input v-model="userDetail.phone" disabled />
              </div>
            </el-form-item>
            <el-form-item label="性别" prop="gender">
              <el-radio-group v-model="formData.gender">
                <el-radio :label="0">未知</el-radio>
                <el-radio :label="1">男</el-radio>
                <el-radio :label="2">女</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="submitLoading" @click="handleSubmit">保存</el-button>
              <el-button @click="handleReset">重置</el-button>
              <el-button type="warning" @click="showChangePasswordDialog = true">修改密码</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <!-- 修改密码对话框 -->
    <el-dialog
      v-model="showChangePasswordDialog"
      title="修改密码"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordFormRules" label-width="100px">
        <el-form-item label="原密码" prop="old_password">
          <el-input
            v-model="passwordForm.old_password"
            type="password"
            placeholder="请输入原密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="passwordForm.new_password"
            type="password"
            placeholder="请输入新密码(6-20位)"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input
            v-model="passwordForm.confirm_password"
            type="password"
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleCancelChangePassword">取消</el-button>
          <el-button type="primary" :loading="passwordSubmitLoading" @click="handleChangePassword">
            确认修改
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts" name="MPUser">
import { ref, reactive, computed, onMounted } from "vue";
import { ElMessage, ElForm, type UploadRequestOptions } from "element-plus";
import { UserFilled, Camera } from "@element-plus/icons-vue";
import { useMPUserStore } from "@/stores/modules/miniprogramUser";
import { changePasswordApi } from "@/api/modules/miniprogram";
import type { UpdateMPUserRequest } from "@/api/modules/miniprogram";
import { uploadImg } from "@/api/modules/upload";
import { encryptPassword } from "@/utils/encrypt";

const mpUserStore = useMPUserStore();

const userInfo = computed(() => mpUserStore.userInfo);
const userDetail = computed(() => mpUserStore.userDetail);

const formRef = ref<InstanceType<typeof ElForm>>();
const submitLoading = ref(false);

const formData = reactive<UpdateMPUserRequest>({
  nickname: "",
  avatar: "",
  gender: 0
});

const formRules = {
  nickname: [{ required: true, message: "请输入昵称", trigger: "blur" }]
};

// 修改密码相关
const showChangePasswordDialog = ref(false);
const passwordFormRef = ref<InstanceType<typeof ElForm>>();
const passwordSubmitLoading = ref(false);

const passwordForm = reactive({
  old_password: "",
  new_password: "",
  confirm_password: ""
});

const validateConfirmPassword = (rule: any, value: any, callback: any) => {
  if (value === "") {
    callback(new Error("请再次输入新密码"));
  } else if (value !== passwordForm.new_password) {
    callback(new Error("两次输入密码不一致"));
  } else {
    callback();
  }
};

const passwordFormRules = {
  old_password: [{ required: true, message: "请输入原密码", trigger: "blur" }],
  new_password: [
    { required: true, message: "请输入新密码", trigger: "blur" },
    { min: 6, max: 20, message: "密码长度为6-20位", trigger: "blur" }
  ],
  confirm_password: [
    { required: true, validator: validateConfirmPassword, trigger: "blur" }
  ]
};

// 初始化表单数据
const initFormData = () => {
  if (userDetail.value) {
    formData.nickname = userDetail.value.nickname || "";
    formData.avatar = userDetail.value.avatar || "";
    formData.gender = 0; // 默认值
  } else if (userInfo.value) {
    formData.nickname = userInfo.value.nickname || "";
    formData.avatar = userInfo.value.avatarUrl || "";
    formData.gender = userInfo.value.gender || 0;
  }
};

// 上传头像前验证
const beforeAvatarUpload = (file: File) => {
  const isImage = file.type.startsWith("image/");
  const isLt2M = file.size / 1024 / 1024 < 2;

  if (!isImage) {
    ElMessage.error("只能上传图片文件！");
    return false;
  }
  if (!isLt2M) {
    ElMessage.error("图片大小不能超过 2MB！");
    return false;
  }
  return true;
};

// 处理头像上传
const handleAvatarUpload = async (options: UploadRequestOptions) => {
  try {
    const formData = new FormData();
    formData.append("file", options.file);

    const { data } = await uploadImg(formData);
    if (data?.fileUrl) {
      formData.avatar = data.fileUrl;
      ElMessage.success("头像上传成功");
      // 立即更新用户信息
      await mpUserStore.updateUserInfo({ avatar: data.fileUrl });
    }
  } catch (error: any) {
    ElMessage.error(error?.msg || "头像上传失败");
  }
};

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return;

  await formRef.value.validate(async valid => {
    if (!valid) return;

    submitLoading.value = true;
    try {
      const success = await mpUserStore.updateUserInfo(formData);
      if (success) {
        ElMessage.success("保存成功");
        await mpUserStore.fetchUserDetail();
      }
    } catch (error: any) {
      ElMessage.error(error?.msg || "保存失败");
    } finally {
      submitLoading.value = false;
    }
  });
};

// 重置表单
const handleReset = () => {
  formRef.value?.resetFields();
  initFormData();
};

// 取消修改密码
const handleCancelChangePassword = () => {
  showChangePasswordDialog.value = false;
  passwordFormRef.value?.resetFields();
};

// 提交修改���码
const handleChangePassword = async () => {
  if (!passwordFormRef.value) return;

  await passwordFormRef.value.validate(async valid => {
    if (!valid) return;

    passwordSubmitLoading.value = true;
    try {
      // 对密码进行MD5加密
      const encryptedOldPassword = encryptPassword(passwordForm.old_password);
      const encryptedNewPassword = encryptPassword(passwordForm.new_password);

      await changePasswordApi({
        old_password: encryptedOldPassword,
        new_password: encryptedNewPassword
      });

      ElMessage.success("密码修改成功，请重新登录");
      showChangePasswordDialog.value = false;
      passwordFormRef.value?.resetFields();

      // 密码修改成功后，延迟1秒后退出登录并跳转到登录页
      setTimeout(() => {
        // 清除用户登录状态
        mpUserStore.resetUser();
        // 跳转到登录页
        window.location.href = "/mp/login";
      }, 1000);
    } catch (error: any) {
      ElMessage.error(error?.msg || "密码修改失败");
    } finally {
      passwordSubmitLoading.value = false;
    }
  });
};

onMounted(async () => {
  // 获取用户详细信息
  if (!mpUserStore.userDetail) {
    await mpUserStore.fetchUserDetail();
  }
  initFormData();
});
</script>

<style scoped lang="scss">
.mp-user {
  .user-info-card {
    .user-avatar-section {
      text-align: center;
      padding: 20px 0;

      .avatar-uploader {
        position: relative;
        display: inline-block;
        margin-bottom: 20px;

        .avatar-mask {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          border-radius: 50%;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          opacity: 0;
          transition: opacity 0.3s;
          cursor: pointer;
          color: white;

          .el-icon {
            font-size: 24px;
            margin-bottom: 5px;
          }

          span {
            font-size: 12px;
          }
        }

        &:hover .avatar-mask {
          opacity: 1;
        }
      }

      .user-name {
        margin: 15px 0 5px;
        font-size: 20px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }

      .user-status {
        margin: 0;
        color: var(--el-text-color-regular);
        font-size: 14px;
      }
    }

    .user-stats {
      .stat-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0;

        .stat-label {
          color: var(--el-text-color-regular);
          font-size: 14px;
        }

        .stat-value {
          font-size: 18px;
          font-weight: 600;
          color: var(--el-color-primary);
        }
      }
    }
  }
}
</style>


















