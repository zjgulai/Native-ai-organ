# Native AI Organ 生产镜像（腾讯云轻量/CVM）
# 多阶段：python 构建静态站 -> nginx 托管 dist
# 构建命令（仓库根目录）：docker build -f deploy/Dockerfile -t native-ai-organ:latest .

FROM python:3.12-slim AS build
WORKDIR /app
COPY . .
RUN python3 build.py --check

FROM nginx:1.27-alpine-slim
LABEL org.opencontainers.image.title="native-ai-organ" \
      org.opencontainers.image.description="Native AI Organ static reading site (books + agent tracks)"

RUN rm -rf /usr/share/nginx/html/* /etc/nginx/conf.d/default.conf
COPY deploy/nginx.conf /etc/nginx/conf.d/native-ai-organ.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8080/healthz >/dev/null || exit 1
