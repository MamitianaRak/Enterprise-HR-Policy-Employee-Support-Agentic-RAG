# Frontend: build the React app, then serve it with nginx.

# ---- Build stage ----
FROM node:24-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . .
RUN npm run build

# ---- Runtime stage: static files + reverse proxy to the API ----
FROM nginx:1.29-alpine

# Rendered at startup with envsubst. API_UPSTREAM is the backend base URL; PORT is set
# by Render (10000) and defaults to 80 for docker compose.
ENV API_UPSTREAM=http://backend:8080 \
    PORT=80 \
    NGINX_ENVSUBST_FILTER="^(API_UPSTREAM|PORT)$"
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD wget -q --spider "http://127.0.0.1:${PORT}/" || exit 1
