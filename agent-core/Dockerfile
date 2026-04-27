# 换用 bookworm（Debian 12），国内镜像源完全支持
FROM python:3.11-slim-bookworm

WORKDIR /app

# ── 换阿里云 bookworm 镜像源 ──────────────────────────
RUN echo "deb https://mirrors.aliyun.com/debian bookworm main\n\
deb https://mirrors.aliyun.com/debian bookworm-updates main\n\
deb https://mirrors.aliyun.com/debian-security bookworm-security main" \
    > /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

COPY . .

RUN mkdir -p /app/data/memory /app/data/files

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]