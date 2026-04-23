"""
Copywriting Library Service - 文案库业务服务

设计目标：
- 独立业务线：不依赖 inspirations / AI对话
- 安全隔离：按 user_id + project_id（IP）进行权限校验
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from loguru import logger
from sqlalchemy import select, and_, func, desc, asc, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.copywriting_library import CopywritingLibraryEntry, CopywritingEntryStatus
from schemas.copywriting_library import (
    CopywritingEntryCreate,
    CopywritingEntryUpdate,
    CopywritingEntryQueryParams,
    CopywritingPublishDataUpdate,
)
from services.resource.project import ProjectService
from utils.exceptions import NotFoundException, BadRequestException
from utils.pagination import PageResult


class CopywritingLibraryService:
    """文案库服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.project_service = ProjectService(db)

    async def _ensure_project_owned(self, user_id: int, project_id: int) -> None:
        """
        校验 project_id 是否属于当前用户。

        这是文案库最重要的安全边界：避免越权写入/读取他人IP下的文案。
        """
        project = await self.project_service.get_project_by_id(project_id, user_id=user_id)
        if not project:
            raise NotFoundException("项目不存在或无权访问")

    async def create_entry(self, user_id: int, data: CopywritingEntryCreate) -> CopywritingLibraryEntry:
        # 1) 校验项目归属
        await self._ensure_project_owned(user_id=user_id, project_id=data.project_id)

        # 2) 创建条目
        entry = CopywritingLibraryEntry(
            user_id=user_id,
            project_id=data.project_id,
            content=data.content,
            status=data.status or CopywritingEntryStatus.TODO.value,
        )
        entry.set_tags_list(data.tags or [])

        self.db.add(entry)
        await self.db.flush()
        await self.db.refresh(entry)

        logger.info(f"文案库条目创建成功: id={entry.id}, user_id={user_id}, project_id={data.project_id}")
        return entry

    async def get_entry_by_id(self, entry_id: int, user_id: int) -> CopywritingLibraryEntry:
        query = (
            select(CopywritingLibraryEntry)
            .where(
                and_(
                    CopywritingLibraryEntry.id == entry_id,
                    CopywritingLibraryEntry.user_id == user_id,
                )
            )
            .options(selectinload(CopywritingLibraryEntry.project))
        )
        result = await self.db.execute(query)
        entry = result.scalar_one_or_none()
        if not entry:
            raise NotFoundException("文案不存在或无权访问")
        return entry

    async def update_entry(
        self, entry_id: int, user_id: int, data: CopywritingEntryUpdate
    ) -> CopywritingLibraryEntry:
        entry = await self.get_entry_by_id(entry_id, user_id)

        # content
        if data.content is not None:
            entry.content = data.content

        # tags
        if data.tags is not None:
            entry.set_tags_list(data.tags)

        # status
        if data.status is not None:
            entry.status = data.status

        await self.db.flush()
        await self.db.refresh(entry)
        return entry

    async def update_publish_data(
        self,
        entry_id: int,
        user_id: int,
        data: CopywritingPublishDataUpdate,
        auto_set_published_status: bool = True,
    ) -> CopywritingLibraryEntry:
        """
        补录发布数据。

        约定：
        - 只要调用此接口，默认会把状态置为 published（可通过 auto_set_published_status 关闭）
        - published_at：若未传入且此前为空，则写入当前时间
        """
        entry = await self.get_entry_by_id(entry_id, user_id)

        if data.views is not None:
            entry.views = data.views
        if data.likes is not None:
            entry.likes = data.likes
        if data.comments is not None:
            entry.comments = data.comments
        if data.shares is not None:
            entry.shares = data.shares

        if data.published_at is not None:
            entry.published_at = data.published_at
        elif entry.published_at is None:
            # 用户没传，但第一次补录时补一个时间，方便后续排序/统计
            entry.published_at = datetime.now()

        if auto_set_published_status:
            entry.status = CopywritingEntryStatus.PUBLISHED.value

        await self.db.flush()
        await self.db.refresh(entry)
        return entry

    async def list_entries(self, user_id: int, params: CopywritingEntryQueryParams) -> PageResult[CopywritingLibraryEntry]:
        # 文案库按 IP 隔离，此处强制要求 project_id
        if not params.project_id:
            raise BadRequestException("project_id 必填（每个IP一套文案库）")

        await self._ensure_project_owned(user_id=user_id, project_id=params.project_id)

        conditions = [
            CopywritingLibraryEntry.user_id == user_id,
            CopywritingLibraryEntry.project_id == params.project_id,
        ]

        if params.status:
            conditions.append(CopywritingLibraryEntry.status == params.status)

        if params.keyword:
            kw = params.keyword.strip()
            if kw:
                conditions.append(CopywritingLibraryEntry.content.like(f"%{kw}%"))

        if params.tag:
            tag = params.tag.strip()
            if tag:
                # MySQL JSON_CONTAINS
                conditions.append(text("JSON_CONTAINS(copywriting_library_entries.tags, :tag)"))

        # 排序字段白名单，避免把 sort_by 直接拼到 SQL
        sort_field = params.sort_by if params.sort_by in ("created_at", "updated_at") else "created_at"
        sort_order = (params.sort_order or "desc").lower()
        order_by_expr = getattr(CopywritingLibraryEntry, sort_field)
        order_by = asc(order_by_expr) if sort_order == "asc" else desc(order_by_expr)

        # count
        count_query = select(func.count(CopywritingLibraryEntry.id)).where(and_(*conditions))
        if params.tag and params.tag.strip():
            count_query = count_query.params(tag=f'["{params.tag.strip()}"]')
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # list
        query = (
            select(CopywritingLibraryEntry)
            .where(and_(*conditions))
            .options(selectinload(CopywritingLibraryEntry.project))
            .order_by(order_by)
            .offset(params.offset)
            .limit(params.pageSize)
        )
        if params.tag and params.tag.strip():
            query = query.params(tag=f'["{params.tag.strip()}"]')
        result = await self.db.execute(query)
        items = result.scalars().all()

        return PageResult(
            list=list(items),
            total=total,
            pageNum=params.pageNum,
            pageSize=params.pageSize,
        )

    async def delete_entry(self, entry_id: int, user_id: int) -> None:
        entry = await self.get_entry_by_id(entry_id, user_id)
        await self.db.delete(entry)
        await self.db.flush()

