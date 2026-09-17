# Two stages. The builder gets the full dependency tree; the runner gets only what Next's
# standalone output actually imports, which is a fraction of node_modules.

FROM node:24-slim AS builder
WORKDIR /app

# Copy manifests alone first, so a source-only change does not re-run the install layer.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# API_URL is read at request time, not baked in here. Build-time would pin the container to
# whichever API existed when the image was built.
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:24-slim AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Non-root. Cloud Run does not require it, but a container that never needs to write as root
# should not be able to.
RUN groupadd --system --gid 1001 nodejs && useradd --system --uid 1001 --gid nodejs nextjs

COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

USER nextjs

# The standalone server binds to localhost unless told otherwise, which listens to nothing
# outside the container. PORT is what Cloud Run injects; 8080 is its default.
ENV HOSTNAME=0.0.0.0
ENV PORT=8080
EXPOSE 8080

# Cloud Run sets $PORT, so it is expanded at runtime. JSON form with an explicit `/bin/sh -c`
# gets that without tripping the JSONArgsRecommended lint. `exec` keeps node as PID 1 so
# SIGTERM reaches it and the container stops cleanly.
CMD ["/bin/sh", "-c", "exec node server.js"]
