# 使用Ubuntu 24.04作为基础镜像
FROM ubuntu:24.04

# 设置工作目录
WORKDIR /app

# 设置环境变量，避免交互式安装提示
ENV DEBIAN_FRONTEND=noninteractive

# 更新包列表并安装必要的系统依赖和Python 3.12
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3.12-venv \
    python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 设置Python 3.12为默认python命令
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1

# 复制项目文件
COPY . /app

# 安装Python依赖
RUN pip install --break-system-packages --no-cache-dir -r requirements.txt

# 设置环境变量
ENV CLOUDFLARE_ACCOUNT_ID=""
ENV CLOUDFLARE_API_TOKEN=""
ENV MODELSCOPE_API_TOKEN=""
ENV DASHSCOPE_API_KEY=""
ENV PORT=5000

# 使用Gunicorn运行Flask应用，动态绑定PORT环境变量
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} app:app"]