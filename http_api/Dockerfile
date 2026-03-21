# NanoBOT HTTP API Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY pyproject.toml .
COPY http_api/requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -e . \
    && pip install --no-cache-dir -r http_api/requirements.txt

# 复制代码
COPY . .

# 创建非 root 用户
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# 暴露端口
EXPOSE 18791

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:18791/health')" || exit 1

# 启动命令
CMD ["uvicorn", "nanobot.http_api.main:app", "--host", "0.0.0.0", "--port", "18791"]