"""
Agent Registry 註冊中心
管理所有 Agents 的註冊、查詢和執行
"""

from typing import Dict, List, Optional, Type, Callable, Any
import logging
from functools import wraps

from .agent_base import BaseAgent
from .types import AgentResponse

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Agent 註冊中心
    負責管理所有已註冊的 Agents，提供查詢、執行等功能
    """

    def __init__(self):
        """初始化註冊中心"""
        self._agents: Dict[str, BaseAgent] = {}
        self._agent_classes: Dict[str, Type[BaseAgent]] = {}

    def register_agent(self, agent: BaseAgent) -> None:
        """
        註冊一個 Agent 實例

        Args:
            agent: 要註冊的 Agent 實例

        Raises:
            TypeError: 當 agent 不是 BaseAgent 的子類時
            ValueError: 當 agent 名稱已存在時
        """
        if not isinstance(agent, BaseAgent):
            raise TypeError(f"Agent 必須是 BaseAgent 的子類，但收到 {type(agent)}")

        if agent.name in self._agents:
            logger.warning(f"Agent '{agent.name}' 已存在，將被覆蓋")

        self._agents[agent.name] = agent
        self._agent_classes[agent.name] = type(agent)
        logger.info(f"已註冊 Agent: {agent.name}")

    def register_agent_class(self, agent_class: Type[BaseAgent], *args, **kwargs) -> None:
        """
        註冊一個 Agent 類別並自動實例化

        Args:
            agent_class: Agent 類別
            *args: 傳遞給 Agent 構造函數的位置參數
            **kwargs: 傳遞給 Agent 構造函數的關鍵字參數

        Raises:
            TypeError: 當 agent_class 不是 BaseAgent 的子類時
        """
        if not issubclass(agent_class, BaseAgent):
            raise TypeError(f"Agent 類別必須是 BaseAgent 的子類，但收到 {agent_class}")

        try:
            agent_instance = agent_class(*args, **kwargs)
            self.register_agent(agent_instance)
        except Exception as e:
            logger.error(f"無法實例化 Agent 類別 {agent_class.__name__}: {e}")
            raise

    def unregister_agent(self, name: str) -> bool:
        """
        取消註冊一個 Agent

        Args:
            name: Agent 名稱

        Returns:
            bool: 是否成功取消註冊
        """
        if name in self._agents:
            del self._agents[name]
            if name in self._agent_classes:
                del self._agent_classes[name]
            logger.info(f"已取消註冊 Agent: {name}")
            return True
        return False

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """
        根據名稱獲取 Agent

        Args:
            name: Agent 名稱

        Returns:
            Optional[BaseAgent]: Agent 實例，如果不存在則返回 None
        """
        return self._agents.get(name)

    def list_agents(self) -> List[BaseAgent]:
        """
        獲取所有已註冊的 Agents

        Returns:
            List[BaseAgent]: 所有已註冊的 Agent 列表
        """
        return list(self._agents.values())

    def get_agent_names(self) -> List[str]:
        """
        獲取所有已註冊的 Agent 名稱

        Returns:
            List[str]: Agent 名稱列表
        """
        return list(self._agents.keys())

    def has_agent(self, name: str) -> bool:
        """
        檢查是否存在指定名稱的 Agent

        Args:
            name: Agent 名稱

        Returns:
            bool: 是否存在
        """
        return name in self._agents

    async def execute_agent(self, name: str, **kwargs) -> AgentResponse:
        """
        執行指定名稱的 Agent

        Args:
            name: Agent 名稱
            **kwargs: 傳遞給 Agent 的參數

        Returns:
            AgentResponse: Agent 執行結果

        Raises:
            ValueError: 當 Agent 不存在時
        """
        agent = self.get_agent(name)
        if not agent:
            error_msg = f"Agent '{name}' 不存在"
            logger.error(error_msg)
            return AgentResponse.error(error_msg)

        try:
            logger.info(f"執行 Agent '{name}' with params: {kwargs}")
            result = await agent.execute(**kwargs)
            logger.info(f"Agent '{name}' 執行完成，狀態: {result.status}")
            return result
        except Exception as e:
            error_msg = f"執行 Agent '{name}' 時發生錯誤: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return AgentResponse.error(error_msg)

    def get_agent_info(self) -> Dict[str, Dict[str, str]]:
        """
        獲取所有 Agent 的資訊

        Returns:
            Dict[str, Dict[str, str]]: Agent 資訊字典，包含名稱、描述和類別名稱
        """
        return {
            name: {
                "name": agent.name,
                "description": agent.description,
                "class": type(agent).__name__
            }
            for name, agent in self._agents.items()
        }

    def clear(self) -> None:
        """清空所有已註冊的 Agents"""
        self._agents.clear()
        self._agent_classes.clear()
        logger.info("已清空所有已註冊的 Agents")

    def __len__(self) -> int:
        """返回已註冊的 Agent 數量"""
        return len(self._agents)

    def __contains__(self, name: str) -> bool:
        """檢查是否包含指定名稱的 Agent"""
        return name in self._agents

    def __iter__(self):
        """迭代所有 Agent"""
        return iter(self._agents.values())


# 全域註冊中心實例
_global_registry = AgentRegistry()


def get_global_registry() -> AgentRegistry:
    """
    獲取全域註冊中心實例

    Returns:
        AgentRegistry: 全域註冊中心
    """
    return _global_registry


def register_agent(name: str = None, description: str = None):
    """
    裝飾器：自動註冊 Agent 類別到全域註冊中心

    Args:
        name: Agent 名稱，如果未提供則使用類別名稱
        description: Agent 描述，如果未提供則使用類別文檔字串

    Returns:
        Callable: 裝飾器函數

    Example:
        @register_agent(name="weather", description="天氣查詢 Agent")
        class WeatherAgent(BaseAgent):
            async def execute(self, **kwargs):
                pass
    """
    def decorator(agent_class: Type[BaseAgent]) -> Type[BaseAgent]:
        if not issubclass(agent_class, BaseAgent):
            raise TypeError(f"只能裝飾 BaseAgent 的子類，但收到 {agent_class}")

        # 確定 Agent 名稱和描述
        agent_name = name or agent_class.__name__.lower().replace('agent', '')
        agent_description = description or agent_class.__doc__ or f"{agent_class.__name__} Agent"

        # 註冊到全域註冊中心
        try:
            agent_instance = agent_class(agent_name, agent_description)
            _global_registry.register_agent(agent_instance)
        except Exception as e:
            logger.error(f"無法註冊 Agent {agent_class.__name__}: {e}")
            raise

        return agent_class

    return decorator


# 向後相容的函數包裝器
def register_function_as_agent(func: Callable, name: str, description: str) -> None:
    """
    將函數包裝為 Agent 並註冊

    Args:
        func: 要包裝的函數
        name: Agent 名稱
        description: Agent 描述

    Note:
        這是為了向後相容現有的函數式 Agent 設計
    """
    class FunctionAgent(BaseAgent):
        def __init__(self, name: str, description: str, func: Callable):
            super().__init__(name, description)
            self.func = func

        async def execute(self, **kwargs) -> AgentResponse:
            try:
                result = await self.func(**kwargs)
                # 如果函數返回的是字典格式，轉換為 AgentResponse
                if isinstance(result, dict):
                    if result.get("status") == "success":
                        return AgentResponse.success(
                            result.get("report", ""),
                            {k: v for k, v in result.items() if k not in ["status", "report", "error_message"]}
                        )
                    elif result.get("status") == "error":
                        return AgentResponse.error(result.get("error_message", "Unknown error"))
                    else:
                        return AgentResponse.success(str(result))
                else:
                    return AgentResponse.success(str(result))
            except Exception as e:
                return AgentResponse.error(f"函數執行錯誤: {str(e)}")

    agent = FunctionAgent(name, description, func)
    _global_registry.register_agent(agent)