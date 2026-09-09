# Frontend: production Vite build served by nginx.

FROM node:22-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# ui/src/config.js reads both of these. Vite inlines import.meta.env at BUILD
# time, so they are build args, not runtime environment variables - changing
# either means rebuilding this image.
#
# It is the browser that calls the backend, so VITE_API_URL must be reachable
# from the host, not the compose network: never http://backend:8000.
#
# localhost, NOT 127.0.0.1: same-site is scheme + registrable domain and
# ignores the port, so localhost:5173 -> localhost:8000 is same-site and the
# SameSite=Lax session cookie is sent, while localhost:5173 ->
# 127.0.0.1:8000 is cross-site and the browser withholds it, leaving the app
# permanently stuck on the sign-in screen. Do not "normalise" this to an IP.
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

# Google OAuth client id. Not a secret - it identifies the app to Google and
# ships in the bundle by design. It must match the backend's GOOGLE_CLIENT_ID,
# which checks the ID token's `aud` claim against its own copy;
# docker-compose.yml interpolates both from the same .env entry so they cannot
# drift. Empty default so a bare `docker build` still succeeds - the app then
# renders an explicit "not configured" message instead of a dead button.
ARG VITE_GOOGLE_CLIENT_ID=
ENV VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID

RUN npm run build

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
