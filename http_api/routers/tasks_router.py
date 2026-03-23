"""任务管理路由"""

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from nanobot.agent.loop import AgentLoop

logger = logging.getLogger(__name__)

router = APIRouter()


def get_agent() -> AgentLoop:
    """依赖注入：获取 Agent 实例（从 app_state）"""
    from ..core.app_state import get_agent
    return get_agent()


@router.post("/tasks/{session_key}/cancel")
async def cancel_task(
    session_key: str,
    agent: AgentLoop = Depends(get_agent),
):
    """
    取消指定会话的任务

    参数：
    - session_key: 会话键，格式为 "user:session_id"

    返回：
    {
        "session_key": "user:session_id",
        "cancelled": 3,
        "message": "Stopped 3 task(s)."
    }
    """
    try:
        if not hasattr(agent, '_active_tasks'):
            raise HTTPException(status_code=500, detail="Agent does not support task cancellation")

        tasks = agent._active_tasks.pop(session_key, [])
        cancelled = 0
        for task in tasks:
            if not task.done():
                task.cancel()
                cancelled += 1
                try:
                    await task
                except (asyncio.CancelledError, Exception):
                    pass

        sub_cancelled = 0
        if hasattr(agent, 'subagents'):
            sub_cancelled = await agent.subagents.cancel_by_session(session_key)

        total = cancelled + sub_cancelled
        message = f"Stopped {total} task(s)." if total else "No active task to stop."

        return {
            "session_key": session_key,
            "cancelled": total,
            "message": message,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"cancel_task_error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{session_key}/status")
async def get_task_status(
    session_key: str,
    agent: AgentLoop = Depends(get_agent),
):
    """
    获取指定会话的任务状态

    参数：
    - session_key: 会话键

    返回：
    {
        "session_key": "user:session_id",
        "active_tasks": 3,
        "has_active_task": true
    }
    """
    try:
        if not hasattr(agent, '_active_tasks'):
            raise HTTPException(status_code=500, detail="Agent does not support task status")

        tasks = agent._active_tasks.get(session_key, [])
        active_count = sum(1 for t in tasks if not t.done())

        return {
            "session_key": session_key,
            "active_tasks": active_count,
            "has_active_task": active_count > 0,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_task_status_error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks")
async def list_tasks(
    agent: AgentLoop = Depends(get_agent),
):
    """
    列出所有活动任务

    返回：
    {
        "tasks": [
            {"session_key": "user:session1", "active_tasks": 2},
            {"session_key": "user:session2", "active_tasks": 0}
        ]
    }
    """
    try:
        if not hasattr(agent, '_active_tasks'):
            raise HTTPException(status_code=500, detail="Agent does not support task listing")

        result = []
        for session_key, tasks in agent._active_tasks.items():
            active_count = sum(1 for t in tasks if not t.done())
            result.append({
                "session_key": session_key,
                "active_tasks": active_count,
            })

        return {"tasks": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"list_tasks_error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
