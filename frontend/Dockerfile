FROM node:22-alpine AS base

WORKDIR /app
RUN corepack enable

FROM base AS dependencies

COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

FROM dependencies AS development

COPY frontend/ ./
EXPOSE 3000
CMD ["pnpm", "dev", "--hostname", "0.0.0.0"]

FROM dependencies AS builder

ARG COMPOSE_FRONTEND_API_BASE_URL=
ARG COMPOSE_FRONTEND_KAKAO_MAP_APP_KEY=
ENV COMPOSE_FRONTEND_API_BASE_URL=$COMPOSE_FRONTEND_API_BASE_URL \
    COMPOSE_FRONTEND_KAKAO_MAP_APP_KEY=$COMPOSE_FRONTEND_KAKAO_MAP_APP_KEY

COPY frontend/ ./
RUN pnpm build

FROM node:22-alpine AS runner

WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs

COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
