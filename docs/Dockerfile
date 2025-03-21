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

FROM httpd:alpine AS lean
ARG CANONICAL_URL="http://define-me.pls"

ENV CANONICAL_URL=$CANONICAL_URL

RUN SERVER_NAME=$(echo "$CANONICAL_URL" | sed -E 's|https?://||' | cut -d'/' -f1) && \
    echo "ServerName ${SERVER_NAME}" >> /usr/local/apache2/conf/httpd.conf

COPY --from=build /app/dist /usr/local/apache2/htdocs/
EXPOSE 80