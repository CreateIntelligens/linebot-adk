"""
基礎架構模組
提供所有 Agent 的基礎類別和通用類型定義
"""

from .agent_base import BaseAgent
from .types import AgentResponse
from .registry import AgentRegistry, get_global_registry, register_agent, register_function_as_agent

__all__ = [
    'BaseAgent',
    'AgentResponse',
    'AgentRegistry',
    'get_global_registry',
    'register_agent',
    'register_function_as_agent'
]