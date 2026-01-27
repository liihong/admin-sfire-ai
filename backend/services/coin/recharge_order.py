"""
充值订单服务
用于处理充值订单的创建、支付回调、状态查询等
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from loguru import logger

from models.compute import ComputeLog, ComputeType
from models.user import User
from services.coin.package import RechargePackageService
from services.coin.account import CoinAccountService
from services.payment.wechat import WeChatPayService
from utils.payment import generate_order_id
from utils.exceptions import NotFoundException, BadRequestException, ServerErrorException


class RechargeOrderService:
    """
    充值订单服务类
    
    职责说明：
    - 订单创建：生成订单号、创建订单记录、调用支付服务
    - 支付回调：验证签名、处理支付成功、充值算力
    - 订单查询：查询订单状态
    """
    
    def __init__(self, db: AsyncSession):
        """
        初始化订单服务
        
        Args:
            db: 异步数据库会话
        """
        self.db = db
        self.package_service = RechargePackageService(db)
        self.account_service = CoinAccountService(db)
        self.payment_service = WeChatPayService()
    
    async def create_order(
        self,
        user_id: int,
        package_id: int,
        openid: str,
        client_ip: str = "127.0.0.1"
    ) -> Dict[str, Any]:
        """
        创建充值订单
        
        流程：
        1. 验证套餐是否存在且启用
        2. 生成唯一订单号
        3. 创建 ComputeLog 记录（状态：pending）
        4. 调用支付服务创建统一下单
        5. 返回支付参数给前端
        
        Args:
            user_id: 用户ID
            package_id: 套餐ID
            openid: 用户openid
            client_ip: 用户IP地址
        
        Returns:
            订单信息和支付参数
        
        Raises:
            NotFoundException: 套餐不存在
            BadRequestException: 套餐未启用或参数错误
            ServerErrorException: 支付服务调用失败
        """
        # 1. 查询套餐信息
        package = await self.package_service.get_package_by_id(package_id)
        
        if package.status != 1:
            raise BadRequestException("套餐未启用，无法购买")
        
        # 2. 获取用户信息（用于记录余额）
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise NotFoundException("用户不存在")
        
        before_balance = user.balance
        
        # 3. 生成订单号（异步函数）
        order_id = await generate_order_id("R")
        
        # 4. 创建订单记录（ComputeLog，状态为pending）
        order_log = ComputeLog(
            user_id=user_id,
            type=ComputeType.RECHARGE,
            amount=package.power_amount,  # 充值算力数量
            before_balance=before_balance,
            after_balance=before_balance,  # 待支付，余额不变
            remark=f"充值订单：{package.name}",
            order_id=order_id,
            package_id=package_id,
            payment_amount=package.price,  # 支付金额（元）
            payment_status="pending",  # 待支付
            source="miniapp"
        )
        self.db.add(order_log)
        await self.db.flush()
        
        # 5. 调用支付服务创建统一下单
        try:
            payment_params = await self.payment_service.create_unified_order(
                order_id=order_id,
                amount=package.price,
                description=f"算力充值-{package.name}",
                openid=openid,
                client_ip=client_ip
            )
        except Exception as e:
            # 支付服务调用失败，更新订单状态为失败并记录错误
            # 订单记录保留，用户可以重试支付或联系客服
            logger.error(
                f"创建支付订单失败: 订单号={order_id}, "
                f"用户ID={user_id}, 套餐ID={package_id}, 错误={e}"
            )
            order_log.payment_status = "failed"
            order_log.remark = f"{order_log.remark}（支付服务调用失败: {str(e)}）"
            await self.db.flush()
            raise ServerErrorException(f"创建支付订单失败: {str(e)}")
        
        # 注意：事务提交由路由层的get_db依赖管理
        
        logger.info(
            f"创建充值订单成功: 订单号={order_id}, "
            f"用户ID={user_id}, 套餐={package.name}, "
            f"金额={package.price}, 算力={package.power_amount}"
        )
        
        return {
            "order_id": order_id,
            "package_id": package_id,
            "package_name": package.name,
            "price": package.price,
            "power_amount": package.power_amount,
            "payment_status": "pending",
            "payment_params": payment_params,
            "created_at": datetime.now(),
        }
    
    async def handle_payment_callback(
        self,
        callback_data: Dict[str, Any],
        sign: str
    ) -> Dict[str, Any]:
        """
        处理支付回调（使用事务确保原子性）
        
        流程：
        1. 验证回调签名
        2. 解析回调数据，获取订单号
        3. 查询订单记录（ComputeLog）
        4. 检查订单状态（防止重复处理）
        5. 调用充值服务充值算力
        6. 更新订单状态为已支付
        7. 记录支付时间和微信交易号
        
        Args:
            callback_data: 回调数据字典
            sign: 回调签名
        
        Returns:
            处理结果
        
        Raises:
            BadRequestException: 签名验证失败或订单状态异常
            NotFoundException: 订单不存在
        """
        # 1. 验证签名
        if not self.payment_service.verify_callback_signature(callback_data, sign):
            # 签名验证失败，记录订单号（如果存在）但不记录完整回调数据（可能包含敏感信息）
            order_id_hint = callback_data.get("out_trade_no", "未知")
            logger.warning(
                f"支付回调签名验证失败: 订单号={order_id_hint}, "
                f"回调参数keys={list(callback_data.keys())}"
            )
            raise BadRequestException("支付回调签名验证失败")
        
        # 2. 解析回调数据
        parsed_data = self.payment_service.parse_callback_data(callback_data)
        order_id = parsed_data.get("order_id")
        transaction_id = parsed_data.get("transaction_id")
        callback_amount = parsed_data.get("amount")  # Decimal类型
        payment_time_str = parsed_data.get("payment_time")
        
        if not order_id:
            raise BadRequestException("回调数据缺少订单号")
        
        # 3. 查询订单记录（使用FOR UPDATE锁定，防止并发处理）
        result = await self.db.execute(
            select(ComputeLog).where(
                and_(
                    ComputeLog.order_id == order_id,
                    ComputeLog.type == ComputeType.RECHARGE
                )
            ).with_for_update()
        )
        order_log = result.scalar_one_or_none()
        
        if not order_log:
            logger.warning(f"订单不存在: {order_id}")
            raise NotFoundException(f"订单 {order_id} 不存在")
        
        # 4. 检查订单状态（防止重复处理）
        if order_log.payment_status == "paid":
            logger.info(f"订单已处理，跳过: {order_id}")
            return {
                "order_id": order_id,
                "status": "already_processed",
                "message": "订单已处理"
            }
        
        if order_log.payment_status not in ["pending", "failed"]:
            raise BadRequestException(f"订单状态异常，无法处理: {order_log.payment_status}")
        
        # 4.5. 验证支付金额（防止金额篡改攻击）
        if order_log.payment_amount and callback_amount:
            # 转换为Decimal进行比较，允许0.01元的误差（微信支付精度）
            expected_amount = Decimal(str(order_log.payment_amount))
            callback_amount_decimal = Decimal(str(callback_amount))
            
            # 计算金额差异
            amount_diff = abs(callback_amount_decimal - expected_amount)
            
            if amount_diff > Decimal("0.01"):
                logger.error(
                    f"支付金额不匹配: 订单号={order_id}, "
                    f"订单金额={expected_amount}元, "
                    f"回调金额={callback_amount_decimal}元, "
                    f"差异={amount_diff}元"
                )
                raise BadRequestException(
                    f"支付金额不匹配，订单异常。订单金额：{expected_amount}元，"
                    f"回调金额：{callback_amount_decimal}元"
                )
        elif not callback_amount:
            logger.warning(f"回调数据缺少支付金额: 订单号={order_id}")
            # 如果订单有金额但回调没有，记录警告但继续处理（可能是测试环境）
        
        # 5. 充值算力（使用账户服务的充值方法）
        try:
            await self.account_service.recharge(
                user_id=order_log.user_id,
                amount=order_log.amount,  # 充值算力数量
                remark=f"充值订单支付成功：{order_log.remark}",
                order_id=order_id
            )
        except Exception as e:
            logger.error(f"充值算力失败: 订单号={order_id}, 错误={e}")
            # 更新订单状态为失败
            order_log.payment_status = "failed"
            await self.db.flush()
            raise ServerErrorException(f"充值算力失败: {str(e)}")
        
        # 6. 更新订单状态
        order_log.payment_status = "paid"
        order_log.wechat_transaction_id = transaction_id
        
        # 解析支付时间
        if payment_time_str:
            try:
                # 微信支付时间格式：yyyyMMddHHmmss
                payment_time = datetime.strptime(payment_time_str, "%Y%m%d%H%M%S")
                order_log.payment_time = payment_time
            except Exception as e:
                logger.warning(f"解析支付时间失败: {payment_time_str}, 错误={e}")
                order_log.payment_time = datetime.now()
        else:
            order_log.payment_time = datetime.now()
        
        # 获取更新后的余额（从recharge方法已更新的用户余额）
        user_result = await self.db.execute(
            select(User.balance).where(User.id == order_log.user_id)
        )
        after_balance = user_result.scalar_one()
        order_log.after_balance = after_balance
        
        await self.db.flush()
        # 注意：事务提交由路由层的get_db依赖管理
        
        logger.info(
            f"支付回调处理成功: 订单号={order_id}, "
            f"用户ID={order_log.user_id}, "
            f"充值算力={order_log.amount}, "
            f"微信交易号={transaction_id}"
        )
        
        return {
            "order_id": order_id,
            "status": "success",
            "message": "支付成功，算力已充值"
        }
    
    async def query_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        查询订单状态
        
        Args:
            order_id: 订单号
        
        Returns:
            订单状态信息
        
        Raises:
            NotFoundException: 订单不存在
        """
        result = await self.db.execute(
            select(ComputeLog).where(
                and_(
                    ComputeLog.order_id == order_id,
                    ComputeLog.type == ComputeType.RECHARGE
                )
            )
        )
        order_log = result.scalar_one_or_none()
        
        if not order_log:
            raise NotFoundException(f"订单 {order_id} 不存在")
        
        return {
            "order_id": order_id,
            "payment_status": order_log.payment_status or "pending",
            "payment_time": order_log.payment_time.isoformat() if order_log.payment_time else None,
            "wechat_transaction_id": order_log.wechat_transaction_id,
        }

