"""
工单服务
用于创建、查询、处理工单，复用 UserService 的充值和等级修改逻辑
"""
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Tuple, Optional

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from loguru import logger

from models.ticket import Ticket, TicketType, TicketStatus
from schemas.ticket import TicketCreate, TicketQueryParams, TicketResponse
from utils.exceptions import BadRequestException, NotFoundException


class TicketService:
    """工单服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _ticket_to_response(self, ticket: Ticket) -> dict:
        """将工单模型转为响应格式"""
        extra_data = None
        if ticket.extra_data:
            try:
                extra_data = json.loads(ticket.extra_data)
            except json.JSONDecodeError:
                extra_data = {}

        return {
            "id": ticket.id,
            "type": ticket.type,
            "status": ticket.status,
            "user_id": ticket.user_id,
            "user": {
                "id": str(ticket.user.id),
                "username": ticket.user.username,
                "phone": ticket.user.phone,
                "nickname": ticket.user.nickname,
            } if ticket.user else None,
            "creator_id": ticket.creator_id,
            "creator": {
                "id": ticket.creator.id,
                "username": ticket.creator.username,
            } if ticket.creator else None,
            "handler_id": ticket.handler_id,
            "handler": {
                "id": ticket.handler.id,
                "username": ticket.handler.username,
            } if ticket.handler else None,
            "is_paid": ticket.is_paid,
            "payment_method": ticket.payment_method,
            "voucher": ticket.voucher,
            "period_type": ticket.period_type,
            "extra_data": extra_data,
            "remark": ticket.remark,
            "handled_at": ticket.handled_at.isoformat() if ticket.handled_at else None,
            "fail_reason": ticket.fail_reason,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
            "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
        }

    async def create_ticket(
        self,
        data: TicketCreate,
        creator_id: int,
    ) -> Ticket:
        """
        创建工单

        Args:
            data: 工单创建参数
            creator_id: 创建人（管理员）ID

        Returns:
            创建的工单对象
        """
        # 校验目标用户存在
        from models.user import User
        user_check = await self.db.execute(select(User).where(User.id == data.user_id, User.is_deleted == False))
        if not user_check.scalar_one_or_none():
            raise NotFoundException(msg=f"用户 {data.user_id} 不存在")

        if data.type == TicketType.MEMBERSHIP:
            if not data.membership:
                raise BadRequestException(msg="会员工单必须填写 membership 详情")
            extra_data = json.dumps({
                "level_code": data.membership.level_code,
                "vip_expire_date": data.membership.vip_expire_date,
            }, ensure_ascii=False)
            ticket = Ticket(
                type=TicketType.MEMBERSHIP,
                status=TicketStatus.PENDING,
                user_id=data.user_id,
                creator_id=creator_id,
                is_paid=data.membership.is_paid,
                payment_method=data.membership.payment_method,
                voucher=data.membership.voucher,
                period_type=data.membership.period_type,
                extra_data=extra_data,
                remark=data.remark,
            )
        elif data.type == TicketType.RECHARGE:
            if not data.recharge:
                raise BadRequestException(msg="充值工单必须填写 recharge 详情")
            extra_data = json.dumps({
                "amount": str(data.recharge.amount),
            }, ensure_ascii=False)
            ticket = Ticket(
                type=TicketType.RECHARGE,
                status=TicketStatus.PENDING,
                user_id=data.user_id,
                creator_id=creator_id,
                extra_data=extra_data,
                remark=data.remark,
            )
        else:
            raise BadRequestException(msg=f"不支持的工单类型: {data.type}")

        self.db.add(ticket)
        await self.db.flush()

        logger.info(
            f"工单已创建: id={ticket.id}, type={ticket.type}, "
            f"user_id={data.user_id}, creator_id={creator_id}"
        )
        return ticket

    async def get_ticket_list(
        self,
        params: TicketQueryParams,
    ) -> Tuple[List[dict], int]:
        """
        获取工单列表（分页）

        Args:
            params: 查询参数

        Returns:
            (工单列表, 总数量)
        """
        conditions = []
        if params.type:
            conditions.append(Ticket.type == params.type)
        if params.status:
            conditions.append(Ticket.status == params.status)
        if params.user_id:
            conditions.append(Ticket.user_id == params.user_id)
        if params.creator_id:
            conditions.append(Ticket.creator_id == params.creator_id)

        # 查询总数
        from sqlalchemy import func
        count_query = select(func.count(Ticket.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页查询（预加载关联）
        offset = (params.pageNum - 1) * params.pageSize
        query = (
            select(Ticket)
            .options(
                selectinload(Ticket.user),
                selectinload(Ticket.creator),
                selectinload(Ticket.handler),
            )
            .order_by(desc(Ticket.created_at))
            .offset(offset)
            .limit(params.pageSize)
        )
        if conditions:
            query = query.where(and_(*conditions))
        result = await self.db.execute(query)
        tickets = result.scalars().all()

        items = [self._ticket_to_response(t) for t in tickets]
        return items, total

    async def get_ticket_by_id(self, ticket_id: int) -> Optional[Ticket]:
        """根据ID获取工单（含关联）"""
        query = (
            select(Ticket)
            .where(Ticket.id == ticket_id)
            .options(
                selectinload(Ticket.user),
                selectinload(Ticket.creator),
                selectinload(Ticket.handler),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_ticket_detail(self, ticket_id: int) -> dict:
        """获取工单详情"""
        ticket = await self.get_ticket_by_id(ticket_id)
        if not ticket:
            raise NotFoundException(msg=f"工单 {ticket_id} 不存在")
        return self._ticket_to_response(ticket)

    async def handle_ticket(
        self,
        ticket_id: int,
        handler_id: int,
    ) -> dict:
        """
        处理工单：执行开通会员或充值算力

        复用 UserService.recharge 和 UserService.change_level

        Args:
            ticket_id: 工单ID
            handler_id: 处理人（管理员）ID

        Returns:
            处理后的工单详情
        """
        ticket = await self.get_ticket_by_id(ticket_id)
        if not ticket:
            raise NotFoundException(msg=f"工单 {ticket_id} 不存在")

        if ticket.status != TicketStatus.PENDING:
            raise BadRequestException(msg=f"工单状态为 {ticket.status}，无法处理")

        # 更新为处理中
        ticket.status = TicketStatus.PROCESSING
        ticket.handler_id = handler_id
        await self.db.flush()

        try:
            from services.user import UserService

            user_service = UserService(self.db)
            extra = json.loads(ticket.extra_data) if ticket.extra_data else {}

            if ticket.type == TicketType.MEMBERSHIP:
                level_code = extra.get("level_code")
                vip_expire_date_str = extra.get("vip_expire_date")
                if not level_code or not vip_expire_date_str:
                    raise BadRequestException(msg="会员工单缺少 level_code 或 vip_expire_date")

                vip_expire_date = None
                try:
                    date_obj = datetime.strptime(vip_expire_date_str, "%Y-%m-%d")
                    vip_expire_date = datetime.combine(
                        date_obj.date(),
                        datetime.max.time(),
                    ).replace(tzinfo=timezone.utc)
                except ValueError:
                    raise BadRequestException(msg="VIP到期时间格式错误，请使用 YYYY-MM-DD")

                await user_service.change_level(
                    user_id=ticket.user_id,
                    level=level_code,
                    vip_expire_date=vip_expire_date,
                    remark=ticket.remark or f"工单#{ticket_id} 开通会员",
                    operator_id=handler_id,
                )

            elif ticket.type == TicketType.RECHARGE:
                amount_str = extra.get("amount")
                if not amount_str:
                    raise BadRequestException(msg="充值工单缺少 amount")
                amount = Decimal(amount_str)

                await user_service.recharge(
                    user_id=ticket.user_id,
                    amount=amount,
                    remark=ticket.remark or f"工单#{ticket_id} 充值算力",
                    operator_id=handler_id,
                )

            else:
                raise BadRequestException(msg=f"不支持的工单类型: {ticket.type}")

            # 处理成功
            ticket.status = TicketStatus.COMPLETED
            ticket.handled_at = datetime.now(timezone.utc)
            ticket.fail_reason = None
            await self.db.flush()

            logger.info(f"工单处理成功: id={ticket_id}, type={ticket.type}, handler_id={handler_id}")

        except Exception as e:
            ticket.status = TicketStatus.FAILED
            ticket.fail_reason = str(e)
            ticket.handled_at = datetime.now(timezone.utc)
            await self.db.flush()
            logger.error(f"工单处理失败: id={ticket_id}, error={e}")
            raise BadRequestException(msg=f"处理失败: {e}")

        # flush 后对象属性可能被 expire，需 refresh 避免异步懒加载触发 MissingGreenlet
        await self.db.refresh(ticket)
        return self._ticket_to_response(ticket)
