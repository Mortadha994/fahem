# Frontend: production Vite build served by nginx.

FROM node:22-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# ui/src/api.js reads import.meta.env.VITE_API_URL. Vite inlines env at BUILD
# time, so this is a build arg, not a runtime environment variable - changing
# the backend URL means rebuilding this image. It is the browser that calls the
# backend, so the value must be reachable from the host, not the compose
# network: 127.0.0.1:8000, never http://backend:8000.
ARG VITE_API_URL=http://127.0.0.1:8000
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
