"""
项目对标抖音账号 — 持久化与权限
"""
from typing import List, Optional

from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from models.project_benchmark import ProjectBenchmarkAccount
from models.project_benchmark_video import ProjectBenchmarkVideo
from services.resource.project import ProjectService
from services.tools.tikhub_douyin import (
    fetch_douyin_user_profile,
    fetch_user_post_videos,
    resolve_sec_uid_from_profile_url,
)
from utils.exceptions import BadRequestException, NotFoundException


class ProjectBenchmarkService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.project_service = ProjectService(db)

    async def _ensure_project(
        self, user_id: int, project_id: int
    ):
        p = await self.project_service.get_project_by_id(
            project_id, user_id=user_id, include_deleted=False
        )
        if not p:
            raise NotFoundException("项目不存在或无权访问")
        return p

    @staticmethod
    def _raise_schema_hint_if_needed(err: Exception) -> None:
        msg = str(err)
        if "Unknown column 'project_benchmark_accounts." in msg:
            raise BadRequestException(
                "数据库缺少对标账号新字段，请先执行迁移 SQL：backend/migrations/alter_project_benchmark_accounts_add_profile_fields.sql"
            )
        if "project_benchmark_videos" in msg:
            raise BadRequestException(
                "数据库缺少对标视频缓存表，请先执行迁移 SQL：backend/migrations/create_project_benchmark_videos.sql"
            )

    async def _get_account(
        self,
        user_id: int,
        project_id: int,
        account_id: int,
    ) -> ProjectBenchmarkAccount:
        await self._ensure_project(user_id, project_id)
        try:
            r = await self.db.execute(
                select(ProjectBenchmarkAccount).where(
                    ProjectBenchmarkAccount.id == account_id,
                    ProjectBenchmarkAccount.project_id == project_id,
                    ProjectBenchmarkAccount.user_id == user_id,
                )
            )
        except OperationalError as e:
            self._raise_schema_hint_if_needed(e)
            raise
        row = r.scalar_one_or_none()
        if not row:
            raise NotFoundException("对标账号不存在或无权访问")
        return row

    async def create(
        self,
        user_id: int,
        project_id: int,
        url: str,
        remark: Optional[str] = None,
    ) -> ProjectBenchmarkAccount:
        await self._ensure_project(user_id, project_id)
        sec_uid = await resolve_sec_uid_from_profile_url(url.strip())
        profile = await self.get_account_profile(sec_uid)
        row = ProjectBenchmarkAccount(
            user_id=user_id,
            project_id=project_id,
            sec_uid=sec_uid,
            profile_url=url.strip()[:1024],
            nickname=str(profile.get("nickname") or "")[:200],
            avatar_url=str(profile.get("avatar_url") or "")[:1024],
            signature=str(profile.get("signature") or "")[:1000],
            follower_count=int(profile.get("follower_count") or 0),
            following_count=int(profile.get("following_count") or 0),
            total_favorited=int(profile.get("total_favorited") or 0),
            aweme_count=int(profile.get("aweme_count") or 0),
            remark=remark,
        )
        self.db.add(row)
        try:
            await self.db.commit()
            await self.db.refresh(row)
        except IntegrityError:
            await self.db.rollback()
            raise BadRequestException("该对标账号已在当前项目中添加过")
        except OperationalError as e:
            await self.db.rollback()
            self._raise_schema_hint_if_needed(e)
            raise
        await self.refresh_videos_cache(user_id, project_id, row.id, limit=40)
        return row

    async def list_by_project(
        self, user_id: int, project_id: int
    ) -> List[ProjectBenchmarkAccount]:
        await self._ensure_project(user_id, project_id)
        try:
            r = await self.db.execute(
                select(ProjectBenchmarkAccount)
                .where(
                    ProjectBenchmarkAccount.project_id == project_id,
                    ProjectBenchmarkAccount.user_id == user_id,
                )
                .order_by(ProjectBenchmarkAccount.created_at.desc())
            )
        except OperationalError as e:
            self._raise_schema_hint_if_needed(e)
            raise
        return list(r.scalars().all())

    async def delete(
        self, user_id: int, project_id: int, account_id: int
    ) -> None:
        row = await self._get_account(user_id, project_id, account_id)
        # 先删除该账号下视频缓存，避免依赖数据库外键级联
        try:
            await self.db.execute(
                delete(ProjectBenchmarkVideo).where(
                    ProjectBenchmarkVideo.user_id == user_id,
                    ProjectBenchmarkVideo.project_id == project_id,
                    ProjectBenchmarkVideo.account_id == account_id,
                )
            )
        except OperationalError as e:
            self._raise_schema_hint_if_needed(e)
            raise
        await self.db.delete(row)
        await self.db.commit()

    async def fetch_videos(
        self,
        user_id: int,
        project_id: int,
        account_id: int,
        max_cursor: int = 0,
        count: int = 20,
    ):
        await self._get_account(user_id, project_id, account_id)
        offset = max(0, int(max_cursor))
        size = max(1, min(int(count), 40))
        try:
            r = await self.db.execute(
                select(ProjectBenchmarkVideo)
                .where(
                    ProjectBenchmarkVideo.user_id == user_id,
                    ProjectBenchmarkVideo.project_id == project_id,
                    ProjectBenchmarkVideo.account_id == account_id,
                )
                .order_by(
                    ProjectBenchmarkVideo.is_top.desc(),
                    ProjectBenchmarkVideo.create_time.desc(),
                    ProjectBenchmarkVideo.id.desc(),
                )
                .offset(offset)
                .limit(size + 1)
            )
        except OperationalError as e:
            self._raise_schema_hint_if_needed(e)
            raise
        rows = list(r.scalars().all())
        has_more = len(rows) > size
        page_rows = rows[:size]
        next_cursor = offset + size if has_more else offset + len(page_rows)
        items = [
            {
                "aweme_id": v.aweme_id,
                "is_top": int(v.is_top or 0),
                "desc": v.desc or "",
                "create_time": int(v.create_time or 0),
                "cover_url": v.cover_url or "",
                "digg_count": int(v.digg_count or 0),
                "comment_count": int(v.comment_count or 0),
                "share_count": int(v.share_count or 0),
                "collect_count": int(v.collect_count or 0),
                "play_count": int(v.play_count or 0),
                "duration": int(v.duration or 0),
                "author_nickname": v.author_nickname or "",
                "author_avatar_url": v.author_avatar_url or "",
                "video_url": v.video_url or "",
                "share_url": v.share_url or "",
            }
            for v in page_rows
        ]
        return items, next_cursor, has_more

    async def get_account(
        self, user_id: int, project_id: int, account_id: int
    ) -> ProjectBenchmarkAccount:
        return await self._get_account(user_id, project_id, account_id)

    async def get_account_profile(self, sec_uid: str) -> dict:
        profile = await fetch_douyin_user_profile(sec_uid)
        if profile.get("nickname") and profile.get("avatar_url"):
            return profile

        # 兜底：部分 sec_uid 在 user/info 无资料时，从作品列表首条作者信息回填。
        try:
            items, _, _ = await fetch_user_post_videos(sec_uid, max_cursor=0, count=1)
            if items:
                first = items[0]
                if not profile.get("nickname"):
                    profile["nickname"] = str(first.get("author_nickname") or "").strip()
                if not profile.get("avatar_url"):
                    profile["avatar_url"] = str(first.get("author_avatar_url") or "").strip()
                if not int(profile.get("follower_count") or 0):
                    profile["follower_count"] = int(first.get("author_follower_count") or 0)
                if not int(profile.get("following_count") or 0):
                    profile["following_count"] = int(first.get("author_following_count") or 0)
                if not int(profile.get("total_favorited") or 0):
                    profile["total_favorited"] = int(first.get("author_total_favorited") or 0)
        except Exception:
            pass
        return profile

    async def refresh_account_profile(
        self, user_id: int, project_id: int, account_id: int
    ) -> ProjectBenchmarkAccount:
        row = await self._get_account(user_id, project_id, account_id)
        profile = await self.get_account_profile(row.sec_uid)
        row.nickname = str(profile.get("nickname") or row.nickname or "")[:200]
        row.avatar_url = str(profile.get("avatar_url") or row.avatar_url or "")[:1024]
        row.signature = str(profile.get("signature") or row.signature or "")[:1000]
        row.follower_count = int(profile.get("follower_count") or row.follower_count or 0)
        row.following_count = int(profile.get("following_count") or row.following_count or 0)
        row.total_favorited = int(profile.get("total_favorited") or row.total_favorited or 0)
        row.aweme_count = int(profile.get("aweme_count") or row.aweme_count or 0)
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def refresh_videos_cache(
        self,
        user_id: int,
        project_id: int,
        account_id: int,
        limit: int = 40,
    ) -> int:
        acc = await self._get_account(user_id, project_id, account_id)
        fetch_count = max(40, int(limit) * 2)
        items, _, _ = await fetch_user_post_videos(acc.sec_uid, max_cursor=0, count=fetch_count)
        # 固化缓存顺序：置顶优先，其次发布时间倒序
        sorted_items = sorted(
            items,
            key=lambda x: (
                -int(x.get("is_top") or 0),
                -int(x.get("create_time") or 0),
            ),
        )[: max(1, min(int(limit), 40))]
        try:
            existing = await self.db.execute(
                select(ProjectBenchmarkVideo).where(
                    ProjectBenchmarkVideo.user_id == user_id,
                    ProjectBenchmarkVideo.project_id == project_id,
                    ProjectBenchmarkVideo.account_id == account_id,
                )
            )
        except OperationalError as e:
            self._raise_schema_hint_if_needed(e)
            raise
        old_rows = list(existing.scalars().all())
        old_map = {x.aweme_id: x for x in old_rows}
        keep_ids: set[str] = set()
        for item in sorted_items:
            aweme_id = str(item.get("aweme_id") or "").strip()
            if not aweme_id:
                continue
            keep_ids.add(aweme_id)
            row = old_map.get(aweme_id)
            if row is None:
                row = ProjectBenchmarkVideo(
                    user_id=user_id,
                    project_id=project_id,
                    account_id=account_id,
                    aweme_id=aweme_id,
                )
                self.db.add(row)
            row.desc = str(item.get("desc") or "")[:2000]
            row.is_top = 1 if int(item.get("is_top") or 0) > 0 else 0
            row.create_time = int(item.get("create_time") or 0)
            row.cover_url = str(item.get("cover_url") or "")[:1024]
            row.digg_count = int(item.get("digg_count") or 0)
            row.comment_count = int(item.get("comment_count") or 0)
            row.share_count = int(item.get("share_count") or 0)
            row.collect_count = int(item.get("collect_count") or 0)
            row.play_count = int(item.get("play_count") or 0)
            row.duration = int(item.get("duration") or 0)
            row.author_nickname = str(item.get("author_nickname") or "")[:200]
            row.author_avatar_url = str(item.get("author_avatar_url") or "")[:1024]
            row.video_url = str(item.get("video_url") or "")[:1024]
            row.share_url = str(item.get("share_url") or "")[:1024]

        for row in old_rows:
            if row.aweme_id not in keep_ids:
                await self.db.delete(row)
        await self.db.commit()
        return len(keep_ids)

    async def refresh_account_and_videos(
        self,
        user_id: int,
        project_id: int,
        account_id: int,
        limit: int = 40,
    ) -> tuple[ProjectBenchmarkAccount, int]:
        row = await self.refresh_account_profile(user_id, project_id, account_id)
        refreshed_count = await self.refresh_videos_cache(
            user_id=user_id,
            project_id=project_id,
            account_id=account_id,
            limit=limit,
        )
        return row, refreshed_count
