"""
会员等级管理服务
处理用户等级变更、降级时的IP冻结等逻辑
"""
from typing import Dict, Any, List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from models.user import User
from models.project import Project, ProjectStatus
from services.system.permission import PermissionService
from utils.redis_lock import RedisLock


class MembershipService:
    """
    会员服务类
    
    职责：
    - 处理用户降级（冻结超出权限的IP）
    - 处理用户升级/续费（解冻IP）
    - 检查并处理过期VIP
    """
    
    # 锁超时时间（秒）
    LOCK_TIMEOUT = 30
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.permission_service = PermissionService(db)
    
    async def handle_user_downgrade(self, user_id: int) -> Dict[str, Any]:
        """
        处理用户降级（核心逻辑）
        
        当用户VIP过期或等级降低时，冻结超出权限的IP
        
        逻辑：
        1. 获取用户当前有效权限（考虑VIP过期）
        2. 查询用户所有正常状态的IP
        3. 如果IP数量超过权限，冻结最晚创建的IP（保留最早创建的）
        
        Args:
            user_id: 用户ID
            
        Returns:
            处理结果字典，包含冻结的IP列表
        """
        # 使用分布式锁防止并发冲突
        lock_value = await RedisLock.acquire_user_downgrade_lock(
            user_id=user_id,
            timeout=self.LOCK_TIMEOUT
        )
        
        if not lock_value:
            logger.warning(f"获取用户降级锁失败: user_id={user_id}，可能正在处理中")
            return {
                "frozen_count": 0,
                "frozen_project_ids": [],
                "message": "降级处理正在进行中，请稍候"
            }
        
        try:
            # 1. 获取用户权限
            permission = await self.permission_service.get_user_permission(user_id)
            max_ip = permission.get("max_ip")
            
            # 如果是不限制，无需处理
            if max_ip is None:
                return {
                    "frozen_count": 0,
                    "frozen_project_ids": [],
                    "message": "您的会员等级不限制IP数量，无需冻结"
                }
            
            # 2. 查询用户所有正常状态的IP（按创建时间倒序）
            query = select(Project).where(
                Project.user_id == user_id,
                Project.is_deleted == False,
                Project.status == ProjectStatus.ACTIVE.value
            ).order_by(desc(Project.created_at))
            
            result = await self.db.execute(query)
            all_projects = result.scalars().all()
            
            # 3. 如果IP数量未超过权限，无需处理
            if len(all_projects) <= max_ip:
                return {
                    "frozen_count": 0,
                    "frozen_project_ids": [],
                    "message": f"当前IP数量({len(all_projects)})未超过权限限制({max_ip})，无需冻结"
                }
            
            # 4. 冻结超出权限的IP（保留最早创建的max_ip个）
            # 注意：all_projects是按创建时间倒序的，所以后面的项目是最晚创建的
            projects_to_freeze = all_projects[max_ip:]
            frozen_ids = []
            
            for project in projects_to_freeze:
                project.status = ProjectStatus.FROZEN.value
                frozen_ids.append(project.id)
                logger.info(
                    f"冻结IP: project_id={project.id}, name={project.name}, "
                    f"user_id={user_id}, created_at={project.created_at}"
                )
            
            await self.db.flush()
            
            logger.info(
                f"用户降级处理完成: user_id={user_id}, "
                f"总IP数={len(all_projects)}, 权限限制={max_ip}, "
                f"冻结数={len(frozen_ids)}, 保留数={max_ip}"
            )
            
            return {
                "frozen_count": len(frozen_ids),
                "frozen_project_ids": frozen_ids,
                "message": f"已冻结 {len(frozen_ids)} 个IP，请续费会员以解锁"
            }
        
        finally:
            # 释放锁
            await RedisLock.release_user_downgrade_lock(
                user_id=user_id,
                lock_value=lock_value
            )
    
    async def handle_user_upgrade(self, user_id: int) -> Dict[str, Any]:
        """
        处理用户升级/续费
        
        当用户升级或续费VIP时，自动解冻所有冻结的IP
        
        Args:
            user_id: 用户ID
            
        Returns:
            处理结果字典，包含解冻的IP列表
        """
        # 查询所有冻结的IP
        query = select(Project).where(
            Project.user_id == user_id,
            Project.is_deleted == False,
            Project.status == ProjectStatus.FROZEN.value
        )
        
        result = await self.db.execute(query)
        frozen_projects = result.scalars().all()
        
        if not frozen_projects:
            return {
                "unfrozen_count": 0,
                "unfrozen_project_ids": [],
                "message": "没有需要解冻的IP"
            }
        
        # 解冻所有IP
        unfrozen_ids = []
        for project in frozen_projects:
            project.status = ProjectStatus.ACTIVE.value
            unfrozen_ids.append(project.id)
            logger.info(
                f"解冻IP: project_id={project.id}, name={project.name}, user_id={user_id}"
            )
        
        await self.db.flush()
        
        logger.info(
            f"用户升级处理完成: user_id={user_id}, 解冻IP数={len(unfrozen_ids)}"
        )
        
        return {
            "unfrozen_count": len(unfrozen_ids),
            "unfrozen_project_ids": unfrozen_ids,
            "message": f"已解冻 {len(unfrozen_ids)} 个IP"
        }
    
    async def check_and_handle_expired_vip(self, user_id: int) -> Dict[str, Any]:
        """
        检查并处理过期VIP（定时任务调用）
        
        Args:
            user_id: 用户ID
            
        Returns:
            处理结果
        """
        permission = await self.permission_service.get_user_permission(user_id)
        
        # 如果VIP已过期，触发降级处理
        if permission.get("is_vip_expired"):
            return await self.handle_user_downgrade(user_id)
        
        return {"message": "VIP未过期，无需处理"}

