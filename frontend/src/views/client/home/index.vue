<template>
  <div class="ip-activation-hall">
    <!-- 背景 -->
    <div class="hall-background"></div>
    
    <!-- 主内容 -->
    <div class="hall-content">
      <div class="hall-header">
        <h1 class="hall-title">IP 激活大厅</h1>
        <p class="hall-subtitle">选择您要激活的 IP 人格</p>
      </div>
      
      <!-- IP 卡片轮播 -->
      <div v-if="loading" class="hall-loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        <p>加载中...</p>
      </div>
      
      <div v-else-if="projects.length === 0" class="hall-empty">
        <el-empty description="暂无 IP 项目">
          <el-button type="primary" @click="goToProject">创建第一个 IP</el-button>
        </el-empty>
      </div>
      
      <div v-else class="hall-cards">
        <Swiper
          :modules="[SwiperEffectCoverflow, SwiperNavigation, SwiperPagination]"
          :effect="'coverflow'"
          :grabCursor="true"
          :centeredSlides="true"
          :slidesPerView="'auto'"
          :coverflowEffect="{
            rotate: 50,
            stretch: 0,
            depth: 100,
            modifier: 1,
            slideShadows: true
          }"
          :navigation="true"
          :pagination="{ clickable: true }"
          class="ip-swiper"
        >
          <SwiperSlide v-for="project in projects" :key="project.id" class="ip-swiper-slide">
            <IPCard :project="project" @click="handleIPActivate" />
          </SwiperSlide>
        </Swiper>
      </div>
      
      <!-- 底部操作 -->
      <div class="hall-footer">
        <el-button type="primary" :icon="Plus" @click="goToProject">创建新 IP</el-button>
        <el-button :icon="FolderOpened" @click="goToProjectList">管理 IP</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts" name="IPActivationHall">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { Loading, Plus, FolderOpened } from "@element-plus/icons-vue";
import { Swiper, SwiperSlide } from "swiper/vue";
import { EffectCoverflow, Navigation, Pagination } from "swiper/modules";
import type SwiperType from "swiper";
import "swiper/css";
import "swiper/css/effect-coverflow";
import "swiper/css/navigation";
import "swiper/css/pagination";
import IPCard from "@/components/IPActivation/IPCard.vue";
import { useIPCreationStore } from "@/stores/modules/ipCreation";
import { getMPProjectListApi } from "@/api/modules/miniprogram";
import type { MPProject } from "@/api/modules/miniprogram";

const router = useRouter();
const ipCreationStore = useIPCreationStore();

const SwiperEffectCoverflow = EffectCoverflow;
const SwiperNavigation = Navigation;
const SwiperPagination = Pagination;

const loading = ref(false);
const projects = ref<MPProject[]>([]);

// 获取项目列表
const fetchProjects = async () => {
  loading.value = true;
  try {
    const { data } = await getMPProjectListApi();
    if (data?.projects) {
      projects.value = data.projects;
    }
  } catch (error: any) {
    ElMessage.error(error?.msg || "获取 IP 列表失败");
  } finally {
    loading.value = false;
  }
};

// 激活 IP
const handleIPActivate = async (project: MPProject) => {
  try {
    // 设置激活的项目
    ipCreationStore.setActiveProject(project);
    
    // 直接跳转到创作中心
    const targetPath = `/mp/workspace/${project.id}`;
    router.push(targetPath).catch((error) => {
      ElMessage.error("路由跳转失败: " + error.message);
    });
  } catch (error: any) {
    ElMessage.error(error?.msg || "激活失败");
  }
};

// 前往项目管理
const goToProject = () => {
  router.push("/mp/project");
};

const goToProjectList = () => {
  router.push("/mp/project");
};

onMounted(async () => {
  await fetchProjects();
});
</script>

<style scoped lang="scss">
.ip-activation-hall {
  position: relative;
  width: 100%;
  min-height: 100vh;
  overflow: hidden;
  
  .hall-background {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: 
      radial-gradient(circle at 20% 30%, rgba(99, 102, 241, 0.08) 0%, transparent 50%),
      radial-gradient(circle at 80% 70%, rgba(236, 72, 153, 0.06) 0%, transparent 50%),
      linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    z-index: 0;
  }
  
  .hall-content {
    position: relative;
    z-index: 1;
    width: 100%;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
  }
  
  .hall-header {
    text-align: center;
    margin-bottom: 48px;
    
    .hall-title {
      font-size: 40px;
      font-weight: 700;
      color: #1f2937;
      margin: 0 0 12px;
      
      @media (max-width: 768px) {
        font-size: 28px;
      }
    }
    
    .hall-subtitle {
      font-size: 16px;
      color: #6b7280;
      margin: 0;
      
      @media (max-width: 768px) {
        font-size: 14px;
      }
    }
  }
  
  .hall-loading,
  .hall-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 0;
    color: #6b7280;
    
    .el-icon {
      font-size: 48px;
      margin-bottom: 16px;
      color: #9ca3af;
    }
  }
  
  .hall-cards {
    width: 100%;
    max-width: 1400px;
    margin: 0 auto 40px;
    
    .ip-swiper {
      width: 100%;
      padding: 40px 0 70px;
      
      :deep(.swiper-slide) {
        width: 320px;
        height: 380px;
        
        @media (max-width: 768px) {
          width: 280px;
          height: 340px;
        }
      }
      
      :deep(.swiper-button-next),
      :deep(.swiper-button-prev) {
        color: #6366f1;
        
        &::after {
          font-size: 24px;
          font-weight: 700;
        }
      }
      
      :deep(.swiper-pagination-bullet) {
        background: #cbd5e1;
        opacity: 1;
      }
      
      :deep(.swiper-pagination-bullet-active) {
        background: #6366f1;
      }
    }
  }
  
  .hall-footer {
    display: flex;
    gap: 16px;
    
    .el-button {
      height: 44px;
      padding: 0 24px;
      font-size: 14px;
      font-weight: 600;
      border-radius: 10px;
    }
    
    @media (max-width: 768px) {
      flex-direction: column;
      width: 100%;
      max-width: 300px;
      
      .el-button {
        width: 100%;
      }
    }
  }
}
</style>
