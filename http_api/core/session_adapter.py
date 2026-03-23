"""会话管理适配器 - 将 NanoBOT SessionManager 适配为 HTTP API 格式"""

from datetime import datetime
from typing import Optional

from nanobot.session.manager import SessionManager, Session

from .models import SessionInfo, SessionDetail


class SessionAdapter:
    """会话管理适配器"""

    def __init__(self, session_mgr: SessionManager):
        self.session_mgr = session_mgr

    def get_or_create(self, user_id: str, chat_id: Optional[str] = None) -> Session:
        """获取或创建会话"""
        if chat_id is None:
            chat_id = user_id
        session_key = f"{user_id}:{chat_id}"
        return self.session_mgr.get_or_create(session_key)

    def get_session_info(self, session: Session) -> SessionInfo:
        """转换为 API 格式"""
        return SessionInfo(
            session_id=session.key,
            user_id=session.key.split(":")[0],
            message_count=len(session.messages),
            created_at=session.created_at,
            updated_at=session.updated_at
        )

    def clear_session(self, user_id: str, chat_id: Optional[str] = None) -> bool:
        """清除会话"""
        if chat_id is None:
            chat_id = user_id
        session_key = f"{user_id}:{chat_id}"
        session = self.session_mgr.get_or_create(session_key)
        if session:
            session.clear()
            return True
        return False

    def list_sessions(self, user_id: Optional[str] = None) -> list[SessionInfo]:
        """列出所有会话"""
        sessions = []
        session_list = self.session_mgr.list_sessions()
        for s in session_list:
            key = s.get("key", "")
            if user_id is None or key.startswith(f"{user_id}:"):
                session_obj = self.session_mgr.get_or_create(key)
                sessions.append(SessionInfo(
                    session_id=key,
                    user_id=key.split(":")[0] if ":" in key else key,
                    message_count=len(session_obj.messages),
                    created_at=datetime.fromisoformat(s.get("created_at", "2020-01-01")) if s.get("created_at") else datetime.now(),
                    updated_at=datetime.fromisoformat(s.get("updated_at", "2020-01-01")) if s.get("updated_at") else datetime.now()
                ))
        return sessions

    def get_session_detail(self, session_id: str) -> Optional[SessionDetail]:
        """获取会话详情"""
        session = self.session_mgr.get_or_create(session_id)
        if not session:
            return None
        return SessionDetail(
            session_id=session.key,
            user_id=session.key.split(":")[0] if ":" in session.key else session.key,
            message_count=len(session.messages),
            created_at=session.created_at,
            updated_at=session.updated_at,
            messages=session.messages
        )
