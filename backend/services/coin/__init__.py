"""
Coin领域服务模块
包含账户管理、计算器、套餐、订单等服务
"""
from .factory import CoinServiceFactory
from .account import CoinAccountService
from .calculator import CoinCalculatorService
from .package import RechargePackageService
from .recharge_order import RechargeOrderService

__all__ = [
    "CoinServiceFactory",  # 主要接口，统一入口
    "CoinAccountService",  # 向后兼容
    "CoinCalculatorService",  # 向后兼容
    "RechargePackageService",  # 套餐服务
    "RechargeOrderService",  # 订单服务
]

