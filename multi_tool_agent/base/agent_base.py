"""
Agent 基礎類別
所有 Agent 都必須繼承此類別並實作 execute 方法
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from .types import AgentResponse


class BaseAgent(ABC):
    """所有 Agent 的基礎類別"""

    def __init__(self, name: str, description: str, auto_register: bool = False):
        """
        初始化 Agent

        Args:
            name: Agent 的名稱
            description: Agent 的功能描述
            auto_register: 是否自動註冊到全域註冊中心
        """
        self.name = name
        self.description = description

        # 延遲導入以避免循環導入
        if auto_register:
            self._auto_register()

    @abstractmethod
    async def execute(self, **kwargs) -> AgentResponse:
        """
        執行 Agent 功能的抽象方法
        子類別必須實作此方法

        Args:
            **kwargs: 執行所需的參數

        Returns:
            AgentResponse: 標準化的回應格式
        """
        pass

    def validate_params(self, required_params: List[str], **kwargs) -> None:
        """
        驗證必要參數是否存在

        Args:
            required_params: 必要參數列表
            **kwargs: 實際傳入的參數

        Raises:
            ValueError: 當缺少必要參數時
        """
        missing = [param for param in required_params if param not in kwargs or kwargs[param] is None]
        if missing:
            raise ValueError(f"缺少必要參數: {missing}")

    def __str__(self) -> str:
        return f"{self.name}: {self.description}"

    def __repr__(self) -> str:
        return f"BaseAgent(name='{self.name}', description='{self.description}')"

    def _auto_register(self) -> None:
        """
        自動註冊到全域註冊中心
        使用延遲導入以避免循環導入問題
        """
        try:
            from .registry import get_global_registry
            registry = get_global_registry()
            registry.register_agent(self)
        except ImportError:
            # 如果無法導入註冊中心，則跳過自動註冊
            pass