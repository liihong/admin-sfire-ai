"""
算力服务工厂
统一入口，封装所有算力相关操作
"""
from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from .account import CoinAccountService
from .calculator import CoinCalculatorService
from services.system.permission import PermissionService
from utils.exceptions import BadRequestException
from models.llm_model import LLMModel


class CoinServiceFactory:
    """
    算力服务工厂类
    
    职责说明：
    - 统一入口：所有算力操作通过工厂提供
    - 服务组合：内部组合 CoinAccountService 和 CoinCalculatorService
    - 业务封装：提供组合操作（如：检查+冻结、结算+记录）
    - 委托模式：基础操作直接委托给底层服务
    
    使用示例：
        factory = CoinServiceFactory(db)
        balance = await factory.get_balance(user_id)
        freeze_result = await factory.check_and_freeze(user_id, model_id, input_text, task_id)
    """
    
    def __init__(self, db: AsyncSession):
        """
        初始化算力服务工厂
        
        Args:
            db: 异步数据库会话
        """
        self.db = db
        self.account_service = CoinAccountService(db)
        self.calculator = CoinCalculatorService(db)
        self.permission_service = PermissionService(db)
    
    # ============== 账户操作（直接委托） ==============
    
    async def get_balance(self, user_id: int) -> dict:
        """
        获取用户余额信息
        
        Args:
            user_id: 用户ID
        
        Returns:
            余额信息字典
        
        Raises:
            BadRequestException: 用户ID无效时
        """
        if user_id <= 0:
            raise BadRequestException("无效的用户ID")
        return await self.account_service.get_user_balance(user_id)
    
    async def recharge(
        self,
        user_id: int,
        amount: Decimal,
        remark: Optional[str] = None,
        operator_id: Optional[int] = None,
        order_id: Optional[str] = None
    ) -> None:
        """
        充值算力
        
        Args:
            user_id: 用户ID
            amount: 充值金额
            remark: 备注
            operator_id: 操作人ID(管理员操作时)
            order_id: 订单ID
        
        Raises:
            BadRequestException: 用户ID或金额无效时
        """
        if user_id <= 0:
            raise BadRequestException("无效的用户ID")
        if amount <= 0:
            raise BadRequestException("充值金额必须大于0")
        if amount > Decimal("1000000"):  # 单次充值上限100万
            raise BadRequestException("单次充值金额不能超过100万火源币")
        
        await self.account_service.recharge(
            user_id=user_id,
            amount=amount,
            remark=remark,
            operator_id=operator_id,
            order_id=order_id
        )
    
    async def adjust(
        self,
        user_id: int,
        amount: Decimal,
        remark: str,
        operator_id: int
    ) -> None:
        """
        管理员调整算力
        
        Args:
            user_id: 用户ID
            amount: 调整金额(正数增加,负数减少)
            remark: 调整原因
            operator_id: 操作人ID
        
        Raises:
            BadRequestException: 用户ID或操作人ID无效时
        """
        if user_id <= 0:
            raise BadRequestException("无效的用户ID")
        if operator_id <= 0:
            raise BadRequestException("无效的操作人ID")
        if not remark or not remark.strip():
            raise BadRequestException("调整原因不能为空")
        
        await self.account_service.adjust(
            user_id=user_id,
            amount=amount,
            remark=remark,
            operator_id=operator_id
        )
    
    # ============== 计算操作（直接委托） ==============
    
    async def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model_id: int
    ) -> Decimal:
        """
        根据实际Token数和模型配置计算算力消耗
        
        Args:
            input_tokens: 输入Token数
            output_tokens: 输出Token数
            model_id: 模型ID
        
        Returns:
            消耗的火源币数量
        """
        return await self.calculator.calculate_cost(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model_id=model_id
        )
    
    async def estimate_max_cost(
        self,
        model_id: int,
        input_text: str,
        estimated_output_tokens: Optional[int] = None
    ) -> Decimal:
        """
        预估最大消耗(用于预冻结)
        
        Args:
            model_id: 模型ID
            input_text: 输入文本
            estimated_output_tokens: 预估输出Token数(如果不提供则使用模型最大值)
        
        Returns:
            预估的最大火源币消耗
        """
        return await self.calculator.estimate_max_cost(
            model_id=model_id,
            input_text=input_text,
            estimated_output_tokens=estimated_output_tokens
        )
    
    def estimate_tokens_from_text(self, text: str) -> int:
        """
        从文本估算Token数
        
        Args:
            text: 输入文本
        
        Returns:
            估算的Token数
        """
        return self.calculator.estimate_tokens_from_text(text)
    
    async def calculate_violation_penalty(self, model_id: int) -> Decimal:
        """
        计算内容违规处罚费用
        
        Args:
            model_id: 模型ID
        
        Returns:
            处罚费用
        """
        return await self.calculator.calculate_violation_penalty(model_id)
    
    def get_cost_breakdown(
        self,
        input_tokens: int,
        output_tokens: int,
        model_id: int,
        model_config: Optional[LLMModel] = None
    ) -> dict:
        """
        获取费用明细
        
        Args:
            input_tokens: 输入Token数
            output_tokens: 输出Token数
            model_id: 模型ID
            model_config: 模型配置(如果已提供则不查询数据库)
        
        Returns:
            费用明细字典
        """
        return self.calculator.get_cost_breakdown(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model_id=model_id,
            model_config=model_config
        )
    
    # ============== 原子操作（直接委托） ==============
    
    async def freeze_amount_atomic(
        self,
        user_id: int,
        amount: Decimal,
        request_id: str,
        model_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
        remark: Optional[str] = None
    ) -> dict:
        """
        原子化冻结算力（幂等性保证 + 乐观锁 CAS）
        
        Args:
            user_id: 用户ID
            amount: 冻结金额
            request_id: 请求ID（全局唯一，用于幂等性）
            model_id: 模型ID（可选）
            conversation_id: 会话ID（可选）
            remark: 备注（可选）
        
        Returns:
            冻结结果字典
        """
        return await self.account_service.freeze_amount_atomic(
            user_id=user_id,
            amount=amount,
            request_id=request_id,
            model_id=model_id,
            conversation_id=conversation_id,
            remark=remark
        )
    
    async def settle_amount_atomic(
        self,
        user_id: int,
        request_id: str,
        actual_cost: Decimal,
        input_tokens: int = 0,
        output_tokens: int = 0,
        model_name: str = "",
        agent_id: Optional[int] = None,
        agent_name: Optional[str] = None
    ) -> dict:
        """
        原子化结算算力（乐观锁 CAS + 解冻 + 扣除）
        
        Args:
            user_id: 用户ID
            request_id: 请求ID
            actual_cost: 实际消耗金额
            input_tokens: 输入Token数
            output_tokens: 输出Token数
            model_name: 模型名称
            agent_id: 智能体ID（可选）
            agent_name: 智能体名称（可选）
        
        Returns:
            结算结果字典
        """
        return await self.account_service.settle_amount_atomic(
            user_id=user_id,
            request_id=request_id,
            actual_cost=actual_cost,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model_name=model_name,
            agent_id=agent_id,
            agent_name=agent_name
        )
    
    async def refund_amount_atomic(
        self,
        user_id: int,
        request_id: str,
        reason: str = "AI生成失败"
    ) -> dict:
        """
        原子化退还算力（乐观锁 CAS + 全额退还）
        
        Args:
            user_id: 用户ID
            request_id: 请求ID
            reason: 退款原因
        
        Returns:
            退款结果字典
        """
        return await self.account_service.refund_amount_atomic(
            user_id=user_id,
            request_id=request_id,
            reason=reason
        )
    
    # ============== 组合操作（工厂封装） ==============
    
    async def check_and_freeze(
        self,
        user_id: int,
        model_id: int,
        input_text: str,
        task_id: str,
        estimated_output_tokens: Optional[int] = None
    ) -> dict:
        """
        检查并冻结算力（组合操作：VIP检查 + 估算 + 冻结）
        
        完整流程：
        1. 检查VIP状态（如果VIP过期，拒绝使用算力）
        2. 估算最大消耗
        3. 原子化冻结（内部会检查余额）
        
        Args:
            user_id: 用户ID
            model_id: 模型ID
            input_text: 输入文本
            task_id: 任务ID
            estimated_output_tokens: 预估输出Token数(可选)
        
        Returns:
            预冻结信息字典
        
        Raises:
            BadRequestException: 余额不足或VIP过期时
        """
        # 输入验证
        if user_id <= 0:
            raise BadRequestException("无效的用户ID")
        if model_id <= 0:
            raise BadRequestException("无效的模型ID")
        if not input_text or not input_text.strip():
            raise BadRequestException("输入文本不能为空")
        if not task_id or not task_id.strip():
            raise BadRequestException("任务ID不能为空")
        
        # 0. 检查VIP状态（如果VIP过期，拒绝使用算力）
        permission = await self.permission_service.get_user_permission(user_id)
        if permission.get("is_vip_expired"):
            raise BadRequestException(
                "您的会员已过期，无法使用算力。请续费会员后再试。"
            )
        
        # 1. 估算最大消耗
        estimated_cost = await self.calculator.estimate_max_cost(
            model_id=model_id,
            input_text=input_text,
            estimated_output_tokens=estimated_output_tokens
        )
        
        logger.debug(
            f"用户 {user_id} 预冻结估算: "
            f"模型ID={model_id}, 预估消耗={estimated_cost}"
        )
        
        # 2. 直接使用原子操作冻结（内部会检查余额）
        freeze_result = await self.account_service.freeze_amount_atomic(
            user_id=user_id,
            amount=estimated_cost,
            request_id=task_id,
            model_id=model_id,
            remark=f"对话预冻结 - 模型ID: {model_id}"
        )
        
        # 3. 检查冻结结果
        if freeze_result['insufficient_balance']:
            # 优化：使用原子操作返回的余额信息（如果包含），避免额外查询
            # 如果原子操作返回了余额信息，直接使用；否则查询一次
            if 'available_balance' in freeze_result:
                available_balance = freeze_result['available_balance']
            else:
                balance_info = await self.account_service.get_user_balance(user_id)
                available_balance = balance_info['available_balance']
            
            raise BadRequestException(
                f"余额不足。可用余额: {available_balance:.4f} 火源币, "
                f"需要: {estimated_cost:.4f} 火源币。"
                f"请充值后再试。"
            )
        
        if not freeze_result['success']:
            logger.error(
                f"❌ [余额检查] 冻结失败: 用户={user_id}, "
                f"task_id={task_id}, result={freeze_result}"
            )
            raise BadRequestException(
                "算力冻结失败，请稍后重试"
            )
        
        logger.debug(
            f"✅ [余额检查] 冻结成功: 用户={user_id}, "
            f"task_id={task_id}, 金额={estimated_cost}, "
            f"freeze_log_id={freeze_result['freeze_log_id']}"
        )
        
        return {
            "task_id": task_id,
            "frozen_amount": estimated_cost,
            "model_id": model_id,
            "user_id": user_id,
            "freeze_log_id": freeze_result['freeze_log_id'],
        }
    
    async def settle_transaction(
        self,
        user_id: int,
        task_id: str,
        actual_cost: Decimal,
        input_tokens: int,
        output_tokens: int,
        model_id: int,
        model_name: str,
        frozen_amount: Decimal,
        is_error: bool = False,
        error_code: Optional[int] = None,
        is_violation: bool = False
    ) -> None:
        """
        结算交易（组合操作：结算 + 错误处理）
        
        根据不同的结算场景：
        - is_error=True: API错误，全额退还
        - is_violation=True: 内容违规，扣除处罚费用
        - 正常完成: 解冻并扣除实际消耗
        
        Args:
            user_id: 用户ID
            task_id: 任务ID
            actual_cost: 实际消耗
            input_tokens: 输入Token数
            output_tokens: 输出Token数
            model_id: 模型ID
            model_name: 模型名称
            frozen_amount: 预冻结金额
            is_error: 是否为错误
            error_code: 错误码
            is_violation: 是否内容违规
        """
        if is_error:
            # API错误,全额退还（使用原子退款）
            reason = "API调用失败"
            await self.account_service.refund_amount_atomic(
                user_id=user_id,
                request_id=task_id,
                reason=reason
            )
        
        elif is_violation:
            # 内容违规,扣除处罚费用
            await self.account_service.deduct_violation_penalty(
                user_id=user_id,
                task_id=task_id,
                model_id=model_id,
                model_name=model_name,
                frozen_amount=frozen_amount
            )
        
        else:
            # ✅ 正常完成,使用原子结算（解冻 + 扣除）
            settle_result = await self.account_service.settle_amount_atomic(
                user_id=user_id,
                request_id=task_id,
                actual_cost=actual_cost,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model_name=model_name
            )
            
            if not settle_result['success']:
                logger.error(
                    f"❌ [结算] 失败: 用户={user_id}, task_id={task_id}, "
                    f"message={settle_result.get('message', '未知错误')}"
                )
                # 结算失败不抛异常，避免影响主流程
                # 但记录错误日志供后续处理
    
    async def deduct_violation_penalty(
        self,
        user_id: int,
        task_id: str,
        model_id: int,
        model_name: str,
        frozen_amount: Decimal
    ) -> None:
        """
        扣除违规处罚费用（委托给账户服务）
        
        Args:
            user_id: 用户ID
            task_id: 关联任务ID
            model_id: 模型ID
            model_name: 模型名称
            frozen_amount: 预冻结金额
        """
        await self.account_service.deduct_violation_penalty(
            user_id=user_id,
            task_id=task_id,
            model_id=model_id,
            model_name=model_name,
            frozen_amount=frozen_amount
        )

