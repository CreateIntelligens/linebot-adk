"""
LINE Bot 指令處理
處理用戶發送的指令(以 ! 開頭)
"""

import logging

logger = logging.getLogger(__name__)


async def handle_command(msg: str, user_id: str, whitelist_manager) -> tuple:
    """
    處理用戶指令

    Args:
        msg (str): 用戶訊息
        user_id (str): 用戶 ID
        whitelist_manager: 白名單管理器實例

    Returns:
        tuple[bool, str]: (是否為指令, 回應訊息)
    """
    if not msg.startswith('!'):
        return False, ""

    command = msg.strip().lower()

    if command == '!加入':
        result = whitelist_manager.add_user(user_id)
        return True, result["message"]

    elif command == '!退出':
        result = whitelist_manager.remove_user(user_id)
        return True, result["message"]

    elif command == '!狀態':
        result = whitelist_manager.get_user_status(user_id)
        return True, result["message"]

    elif command == '!清單':
        result = whitelist_manager.get_all_users(user_id)
        return True, result["message"]

    elif command.startswith('!強制加入 '):
        target_user_id = command.replace('!強制加入 ', '').strip()
        if not target_user_id:
            return True, "❌ 請提供要加入的用戶 ID\n格式：!強制加入 [用戶ID]"
        result = whitelist_manager.admin_add_user(user_id, target_user_id)
        return True, result["message"]

    elif command.startswith('!強制移除 '):
        target_user_id = command.replace('!強制移除 ', '').strip()
        if not target_user_id:
            return True, "❌ 請提供要移除的用戶 ID\n格式：!強制移除 [用戶ID]"
        result = whitelist_manager.admin_remove_user(user_id, target_user_id)
        return True, result["message"]

    else:
        return True, "❌ 未知指令\n\n可用指令：\n• !加入 - 加入測試模式\n• !退出 - 退出測試模式\n• !狀態 - 查看當前狀態\n• !清單 - 查看測試用戶（管理員）"
