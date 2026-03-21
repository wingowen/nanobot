"""会话管理路由"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from nanobot.session.manager import SessionManager

from ..core.session_adapter import SessionAdapter
from ..core.models import SessionInfo

logger = logging.getLogger(__name__)

router = APIRouter()


def get_session_adapter() -> SessionAdapter:
    """依赖注入：获取会话适配器（从全局 app_state）"""
    from ..core.app_state import get_session_manager
    session_mgr = get_session_manager()
    return SessionAdapter(session_mgr)


@router.get("/sessions", response_model=list[SessionInfo])
async def list_sessions(
    user_id: Optional[str] = None,
    adapter: SessionAdapter = Depends(get_session_adapter),
):
    """
    列出所有会话或指定用户的会话
    
    参数：
    - user_id: 可选，过滤特定用户的会话
    """
    try:
        sessions = adapter.list_sessions(user_id)
        return [SessionInfo(**s.dict()) for s in sessions]
    except Exception as e:
        logger.error("list_sessions_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    adapter: SessionAdapter = Depends(get_session_adapter),
):
    """
    获取指定会话的详细信息
    
    包括消息历史、创建时间等
    """
    try:
        # TODO: 实现获取单个会话详情
        return {"session_id": session_id, "status": "not_implemented"}
    except Exception as e:
        logger.error("get_session_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    adapter: SessionAdapter = Depends(get_session_adapter),
):
    """
    删除指定会话
    """
    try:
        # TODO: 实现删除会话
        return {"session_id": session_id, "deleted": True}
    except Exception as e:
        logger.error("delete_session_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/clear")
async def clear_session(
    session_id: str,
    adapter: SessionAdapter = Depends(get_session_adapter),
):
    """
    清空会话消息（保留会话记录）
    """
    try:
        # TODO: 实现清空会话
        return {"session_id": session_id, "cleared": True}
    except Exception as e:
        logger.error("clear_session_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))