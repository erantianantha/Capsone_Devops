# ---- build stage: compile the React app with Node ----
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

# ---- runtime stage: serve static files with unprivileged Nginx ----
FROM nginxinc/nginx-unprivileged:1.29-alpine
# nginx-unprivileged runs as uid 101 and listens on 8080 (no root needed)
ENV BACKEND_URL=http://backend:8000
# Pick up Alpine security patches released after the base image was built
USER root
RUN apk upgrade --no-cache
COPY --chown=101:101 nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build --chown=101:101 /app/dist /usr/share/nginx/html
USER 101
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s --retries=3 CMD wget -qO- http://127.0.0.1:8080/healthz || exit 1
