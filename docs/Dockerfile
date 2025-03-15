### Build stage
FROM node:alpine AS base
ARG K8S_APP__VERSION="unknown"
ARG CANONICAL_URL="http://define-me.pls"

WORKDIR /app

ENV K8S_APP__VERSION=$K8S_APP__VERSION
ENV CANONICAL_URL=$CANONICAL_URL

# By copying only the package.json and package-lock.json here, we ensure that the following `-deps` steps are independent of the source code.
# Therefore, the `-deps` steps will be skipped if only the source code changes.
COPY package.json pnpm-lock.yaml ./

RUN corepack enable && corepack prepare pnpm@9.15.0 --activate

FROM base AS build
COPY . .
RUN pnpm install --frozen-lockfile
RUN pnpm run build

FROM base AS lean
COPY --from=build /app/dist ./dist

ENV HOST=0.0.0.0
ENV PORT=80
EXPOSE 80
CMD ["node", "./dist/server/entry.mjs"]