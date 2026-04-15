"""工具列表路由"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from nanobot.agent.tools.registry import ToolRegistry

from ..core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


def get_tool_registry() -> ToolRegistry:
    """依赖注入：获取工具注册表（从全局状态）"""
    from ..core.app_state import get_agent
    agent = get_agent()
    if hasattr(agent, 'tools') and agent.tools:
        return agent.tools
    # 回退：返回空注册表
    return ToolRegistry()


@router.get("/tools")
async def list_tools(
    category: Optional[str] = None,
    registry: ToolRegistry = Depends(get_tool_registry),
):
    """
    列出所有可用工具
    
    参数：
    - category: 可选，按类别过滤（exec、web、file等）
    """
    try:
        # 使用 get_definitions() 获取工具定义
        tools = registry.get_definitions()
        
        if category:
            tools = [t for t in tools if t.get("category") == category]
            
        return {
            "tools": tools,
            "total": len(tools),
        }
    except Exception as e:
        logger.error("list_tools_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/{tool_name}")
async def get_tool_info(
    tool_name: str,
    registry: ToolRegistry = Depends(get_tool_registry),
):
    """
    获取指定工具的详细信息
    """
    try:
        tool = registry.get(tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
            
        return {
            "name": tool_name,
            "description": tool.description,
            "parameters": tool.parameters,
            "category": getattr(tool, "category", "custom"),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_tool_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/categories")
async def list_tool_categories(
    registry: ToolRegistry = Depends(get_tool_registry),
):
    """
    列出所有工具类别
    """
    try:
        tools = registry.get_definitions()
        categories = set()
        for tool in tools:
            cat = tool.get("category", "custom")
            categories.add(cat)
            
        return {
            "categories": sorted(list(categories)),
            "total": len(categories),
        }
    except Exception as e:
        logger.error("list_categories_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))