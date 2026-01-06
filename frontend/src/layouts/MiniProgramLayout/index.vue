<!-- 小程序用户布局 - 简洁布局，无侧边栏 -->
<template>
  <el-container class="mp-layout" :class="{ 'is-fullscreen': isFullscreen }">
    <el-header v-if="!isFullscreen" class="mp-header">
      <div class="header-left">
        <div class="logo">
          <img class="logo-img" src="@/assets/images/logo.svg" alt="logo" />
          <span class="logo-text">{{ title }}</span>
        </div>
        <el-menu
          :default-active="activeMenu"
          mode="horizontal"
          :router="true"
          class="mp-menu"
        >
          <el-menu-item index="/mp/home">
            <el-icon><HomeFilled /></el-icon>
            <span>首页</span>
          </el-menu-item>
          <el-menu-item index="/mp/project">
            <el-icon><FolderOpened /></el-icon>
            <span>我的项目</span>
          </el-menu-item>
          <el-menu-item index="/mp/data">
            <el-icon><DataAnalysis /></el-icon>
            <span>数据统计</span>
          </el-menu-item>
        </el-menu>
      </div>
      <div class="header-right">
        <div class="user-info">
          <el-avatar :src="userInfo.avatarUrl" :size="32">
            <el-icon><UserFilled /></el-icon>
          </el-avatar>
          <span class="username">{{ userInfo.nickname || "用户" }}</span>
        </div>
        <el-dropdown @command="handleCommand">
          <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="user">
                <el-icon><User /></el-icon>
                <span>个人中心</span>
              </el-dropdown-item>
              <el-dropdown-item divided command="logout">
                <el-icon><SwitchButton /></el-icon>
                <span>退出登录</span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>
    <el-main class="mp-main">
      <router-view v-slot="{ Component, route }">
        <transition appear name="fade-transform" mode="out-in">
          <keep-alive>
            <component :is="Component" v-if="isRouterShow" :key="route.fullPath" />
          </keep-alive>
        </transition>
      </router-view>
    </el-main>
  </el-container>
</template>

<script setup lang="ts" name="MiniProgramLayout">
import { ref, computed, provide } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  HomeFilled,
  FolderOpened,
  DataAnalysis,
  UserFilled,
  User,
  SwitchButton,
  ArrowDown
} from "@element-plus/icons-vue";
import { useMPUserStore } from "@/stores/modules/miniprogramUser";
import { MP_LOGIN_URL } from "@/config";

const title = import.meta.env.VITE_GLOB_APP_TITLE;
const route = useRoute();
const router = useRouter();
const mpUserStore = useMPUserStore();

const isRouterShow = ref(true);
const refreshCurrentPage = (val: boolean) => (isRouterShow.value = val);
provide("refresh", refreshCurrentPage);

const userInfo = computed(() => mpUserStore.userInfo);
const activeMenu = computed(() => route.path);
const isFullscreen = computed(() => route.meta.isFull === true);

// 处理下拉菜单命令
const handleCommand = async (command: string) => {
  if (command === "user") {
    router.push("/mp/user");
  } else if (command === "logout") {
    try {
      await ElMessageBox.confirm("确定要退出登录吗？", "提示", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning"
      });
      mpUserStore.resetUser();
      router.replace(MP_LOGIN_URL);
      ElMessage.success("已退出登录");
    } catch {
      // 用户取消
    }
  }
};
</script>

<style lang="scss">
@use "@/styles/ip-os-theme.scss" as *;
</style>

<style scoped lang="scss">

.mp-layout {
  height: 100vh;
  overflow: hidden;
  
  &.is-fullscreen {
    background: var(--ip-os-bg-primary);
  }
}

.mp-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);

  .header-left {
    display: flex;
    align-items: center;
    flex: 1;

    .logo {
      display: flex;
      align-items: center;
      margin-right: 40px;

      .logo-img {
        width: 32px;
        height: 32px;
        margin-right: 10px;
      }

      .logo-text {
        font-size: 18px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }
    }

    .mp-menu {
      border-bottom: none;
      background: transparent;

      :deep(.el-menu-item) {
        border-bottom: 2px solid transparent;
        transition: all 0.3s;

        &.is-active {
          border-bottom-color: var(--el-color-primary);
          color: var(--el-color-primary);
        }
      }
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 12px;

    .user-info {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 0 12px;

      .username {
        font-size: 14px;
        color: var(--el-text-color-primary);
        max-width: 100px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }

    .dropdown-icon {
      cursor: pointer;
      color: var(--el-text-color-regular);
      transition: color 0.3s;

      &:hover {
        color: var(--el-color-primary);
      }
    }
  }
}

.mp-main {
  padding: 20px;
  background: var(--el-bg-color-page);
  overflow-y: auto;
}

.mp-layout.is-fullscreen {
  .mp-main {
    padding: 0;
    height: 100vh;
    overflow: hidden;
  }
}

// 路由过渡动画
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: all 0.3s;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>


