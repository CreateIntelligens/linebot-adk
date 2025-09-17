"""
通用類型定義
定義所有 Agent 共用的資料類型和回應格式
"""

from typing import Dict, Any, Literal, Optional
from dataclasses import dataclass, field


@dataclass
class AgentResponse:
    """
    標準化的 Agent 回應格式
    所有 Agent 的 execute 方法都應該回傳此類型
    """
    status: Literal["success", "error", "not_relevant"]
    report: str = ""
    error_message: str = ""
    data: Optional[Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        將 AgentResponse 轉換為字典格式
        用於向後相容現有的函數回傳格式

        Returns:
            Dict[str, Any]: 包含狀態和資料的字典，data 中的內容會被展開到頂層
        """
        result = {
            "status": self.status,
            "report": self.report,
            "error_message": self.error_message,
        }

        # 將 data 中的內容展開到頂層，保持向後相容
        if self.data:
            result.update(self.data)

        return result

    @classmethod
    def success(cls, report: str, data: Optional[Dict[str, Any]] = None) -> 'AgentResponse':
        """
        建立成功回應的便利方法

        Args:
            report: 成功訊息
            data: 額外資料

        Returns:
            AgentResponse: 成功狀態的回應
        """
        return cls(status="success", report=report, data=data or {})

    @classmethod
    def error(cls, error_message: str, data: Optional[Dict[str, Any]] = None) -> 'AgentResponse':
        """
        建立錯誤回應的便利方法

        Args:
            error_message: 錯誤訊息
            data: 額外資料

        Returns:
            AgentResponse: 錯誤狀態的回應
        """
        return cls(status="error", error_message=error_message, data=data or {})

    @classmethod
    def not_relevant(cls, message: str = "此請求與當前 Agent 功能不相關") -> 'AgentResponse':
        """
        建立不相關回應的便利方法

        Args:
            message: 不相關的說明訊息

        Returns:
            AgentResponse: 不相關狀態的回應
        """
        return cls(status="not_relevant", report=message)