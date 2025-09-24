# =============================================================================
# whitelist_manager.py - 動態白名單管理系統
# 提供測試用戶白名單的增刪查改功能，支援持久化存儲
# =============================================================================

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class WhitelistManager:
    """
    動態白名單管理器

    負責管理測試用戶白名單，支援動態增刪用戶、持久化存儲、
    以及管理員權限控制等功能。
    """

    def __init__(self, whitelist_file: str = "data/test_whitelist.json"):
        """
        初始化白名單管理器

        Args:
            whitelist_file (str): 白名單檔案路徑
        """
        self.whitelist_file = Path(whitelist_file)
        self.admin_users = self._load_admin_users()
        self._ensure_whitelist_file()

    def _load_admin_users(self) -> List[str]:
        """從環境變數載入管理員用戶ID列表"""
        admin_env = os.getenv("ADMIN_USER_IDS", "")
        admin_list = [user_id.strip() for user_id in admin_env.split(",") if user_id.strip()]
        logger.info(f"載入管理員用戶: {admin_list}")
        return admin_list

    def _ensure_whitelist_file(self):
        """確保白名單檔案存在，不存在則創建"""
        if not self.whitelist_file.exists():
            # 確保父目錄存在
            self.whitelist_file.parent.mkdir(parents=True, exist_ok=True)
            # 創建空白名單檔案
            self._save_whitelist_data({
                "users": [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            })
            logger.info(f"已創建白名單檔案: {self.whitelist_file}")

    def _load_whitelist_data(self) -> Dict[str, Any]:
        """載入白名單數據"""
        try:
            with open(self.whitelist_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"載入白名單檔案失敗: {e}")
            # 返回預設空數據
            return {
                "users": [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

    def _save_whitelist_data(self, data: Dict[str, Any]):
        """儲存白名單數據"""
        try:
            data["updated_at"] = datetime.now().isoformat()
            # 確保父目錄存在
            self.whitelist_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.whitelist_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"白名單數據已儲存: {len(data['users'])} 個用戶")
        except Exception as e:
            logger.error(f"儲存白名單檔案失敗: {e}")
            raise

    def is_in_whitelist(self, user_id: str) -> bool:
        """
        檢查用戶是否在白名單中

        Args:
            user_id (str): LINE 用戶 ID

        Returns:
            bool: 是否在白名單中
        """
        data = self._load_whitelist_data()
        return user_id in data.get("users", [])

    def add_user(self, user_id: str) -> Dict[str, Any]:
        """
        將用戶加入白名單

        Args:
            user_id (str): LINE 用戶 ID

        Returns:
            dict: 操作結果
                - success: 是否成功
                - message: 結果訊息
                - user_count: 目前白名單用戶數
        """
        try:
            data = self._load_whitelist_data()
            users = data.get("users", [])

            if user_id in users:
                return {
                    "success": False,
                    "message": "你已經在測試模式中了！",
                    "user_count": len(users)
                }

            users.append(user_id)
            data["users"] = users
            self._save_whitelist_data(data)

            logger.info(f"用戶 {user_id} 已加入白名單")
            return {
                "success": True,
                "message": "✅ 已加入測試模式！\n現在只會回應三立電視知識庫內容。\n輸入「!退出」可離開測試模式。",
                "user_count": len(users)
            }

        except Exception as e:
            logger.error(f"加入用戶到白名單失敗: {e}")
            return {
                "success": False,
                "message": "加入測試模式失敗，請稍後再試。",
                "user_count": 0
            }

    def remove_user(self, user_id: str) -> Dict[str, Any]:
        """
        將用戶從白名單移除

        Args:
            user_id (str): LINE 用戶 ID

        Returns:
            dict: 操作結果
        """
        try:
            data = self._load_whitelist_data()
            users = data.get("users", [])

            if user_id not in users:
                return {
                    "success": False,
                    "message": "你本來就不在測試模式中！",
                    "user_count": len(users)
                }

            users.remove(user_id)
            data["users"] = users
            self._save_whitelist_data(data)

            logger.info(f"用戶 {user_id} 已從白名單移除")
            return {
                "success": True,
                "message": "✅ 已退出測試模式！\n現在恢復完整的 AI 助手功能。",
                "user_count": len(users)
            }

        except Exception as e:
            logger.error(f"從白名單移除用戶失敗: {e}")
            return {
                "success": False,
                "message": "退出測試模式失敗，請稍後再試。",
                "user_count": 0
            }

    def get_user_status(self, user_id: str) -> Dict[str, Any]:
        """
        獲取用戶當前狀態

        Args:
            user_id (str): LINE 用戶 ID

        Returns:
            dict: 用戶狀態資訊
        """
        data = self._load_whitelist_data()
        users = data.get("users", [])
        is_in_whitelist = user_id in users

        return {
            "user_id": user_id,
            "in_test_mode": is_in_whitelist,
            "total_test_users": len(users),
            "message": "🔧 測試模式：開啟\n只回應三立電視知識庫內容" if is_in_whitelist else "🤖 正常模式：開啟\n完整 AI 助手功能"
        }

    def is_admin(self, user_id: str) -> bool:
        """
        檢查用戶是否為管理員

        Args:
            user_id (str): LINE 用戶 ID

        Returns:
            bool: 是否為管理員
        """
        return user_id in self.admin_users

    def get_all_users(self, requester_user_id: str) -> Dict[str, Any]:
        """
        獲取所有白名單用戶（僅管理員可用）

        Args:
            requester_user_id (str): 請求者的用戶 ID

        Returns:
            dict: 用戶列表或錯誤訊息
        """
        if not self.is_admin(requester_user_id):
            return {
                "success": False,
                "message": "❌ 權限不足，此功能僅限管理員使用。"
            }

        data = self._load_whitelist_data()
        users = data.get("users", [])

        if not users:
            message = "📝 目前沒有用戶在測試模式中"
        else:
            user_list = "\n".join([f"• {user_id}" for user_id in users])
            message = f"📝 測試模式用戶清單 ({len(users)} 人):\n{user_list}"

        return {
            "success": True,
            "message": message,
            "users": users,
            "count": len(users)
        }

    def admin_add_user(self, admin_user_id: str, target_user_id: str) -> Dict[str, Any]:
        """
        管理員強制加入用戶到白名單

        Args:
            admin_user_id (str): 管理員用戶 ID
            target_user_id (str): 目標用戶 ID

        Returns:
            dict: 操作結果
        """
        if not self.is_admin(admin_user_id):
            return {
                "success": False,
                "message": "❌ 權限不足，此功能僅限管理員使用。"
            }

        result = self.add_user(target_user_id)
        if result["success"]:
            result["message"] = f"✅ 管理員操作成功！\n已將用戶 {target_user_id} 加入測試模式。"

        return result

    def admin_remove_user(self, admin_user_id: str, target_user_id: str) -> Dict[str, Any]:
        """
        管理員強制從白名單移除用戶

        Args:
            admin_user_id (str): 管理員用戶 ID
            target_user_id (str): 目標用戶 ID

        Returns:
            dict: 操作結果
        """
        if not self.is_admin(admin_user_id):
            return {
                "success": False,
                "message": "❌ 權限不足，此功能僅限管理員使用。"
            }

        result = self.remove_user(target_user_id)
        if result["success"]:
            result["message"] = f"✅ 管理員操作成功！\n已將用戶 {target_user_id} 移出測試模式。"

        return result

# 全域白名單管理器實例
whitelist_manager = WhitelistManager()