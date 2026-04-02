"""Archiving Session Manager - 继承扩展，支持会话归档和删除功能"""

import json
from pathlib import Path
from typing import Any

from loguru import logger

from nanobot.session.manager import SessionManager, Session
from nanobot.utils.helpers import ensure_dir, safe_filename


class ArchivingSessionManager(SessionManager):
    """支持归档的 SessionManager（继承扩展，无侵入式修改）"""

    def __init__(self, workspace: Path):
        super().__init__(workspace)
        self.archive_dir = ensure_dir(workspace / "sessions_archive")

    def _get_archive_path(self, key: str) -> Path:
        """获取归档文件路径"""
        safe_key = safe_filename(key.replace(":", "_"))
        return self.archive_dir / f"{safe_key}.jsonl"

    def _sync_to_archive(self, session: Session) -> None:
        """同步会话内容到归档文件（追加写入）"""
        archive_path = self._get_archive_path(session.key)

        # 使用 metadata 计数器（支持 /new 后继续归档）
        synced = session.metadata.get("_synced_to_archive")
        if synced is not None:
            new_messages = session.messages[synced:]
        else:
            # 向后兼容：从归档文件行数推断
            archive_line_count = 0
            if archive_path.exists():
                try:
                    with open(archive_path, encoding="utf-8") as f:
                        archive_line_count = sum(1 for line in f if line.strip())
                except Exception:
                    archive_line_count = 0

            # 如果归档行数大于会话消息数（例如 /new 后），从头开始
            if archive_line_count > len(session.messages):
                synced = 0
            else:
                synced = archive_line_count
            new_messages = session.messages[synced:]

        if not new_messages:
            return

        try:
            with open(archive_path, "a", encoding="utf-8") as f:
                for msg in new_messages:
                    f.write(json.dumps(msg, ensure_ascii=False) + "\n")
            session.metadata["_synced_to_archive"] = len(session.messages)
            logger.debug("Synced {} messages to archive {}", len(new_messages), archive_path)
        except Exception:
            logger.exception("Failed to sync archive {}", archive_path)

    def save(self, session: Session) -> None:
        """重写 save 方法，添加归档逻辑"""
        # 先同步到归档
        self._sync_to_archive(session)
        # 调用父类保存
        super().save(session)
