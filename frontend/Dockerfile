FROM node:24.8-alpine AS base

WORKDIR /app

FROM base AS deps
COPY package-lock.json package.json ./
RUN npm ci --only=production --ignore-scripts && \
    cp -R node_modules /tmp/production_node_modules
RUN npm ci --ignore-scripts

FROM base AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY . .

RUN npm run build

FROM nginx:alpine AS production
COPY --from=builder /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
