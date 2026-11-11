# Proje      : SEXSOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : Dockerfile
# Açıklama   : Web ve kalıcı worker için ayrı dağıtım hedefleri.
FROM node:24.12.0-bookworm-slim AS base
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
FROM base AS dependencies
COPY package.json package-lock.json ./
RUN npm ci
FROM dependencies AS builder
COPY . .
RUN npm run build
FROM base AS web
ENV NODE_ENV=production HOSTNAME=0.0.0.0 PORT=3000
RUN groupadd --system app && useradd --system --gid app app
COPY --from=builder --chown=app:app /app/.next/standalone ./
COPY --from=builder --chown=app:app /app/.next/static ./.next/static
COPY --from=builder --chown=app:app /app/public ./public
COPY --from=builder --chown=app:app /app/assets ./assets
USER app
EXPOSE 3000
CMD ["node", "server.js"]
FROM dependencies AS worker
COPY src ./src
COPY scripts ./scripts
COPY migrations ./migrations
COPY tsconfig.json ./tsconfig.json
RUN groupadd --system app && useradd --system --gid app app
USER app
CMD ["node", "--import", "tsx", "scripts/worker.ts"]
