# STAGE 1 - Build
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build && \
    echo "=== Checking .next directory ===" && \
    ls -la .next/ && \
    cat .next/BUILD_ID

# STAGE 2 - Production
FROM node:18-alpine

WORKDIR /app

ENV NODE_ENV=production

COPY package*.json ./
RUN npm install --omit=dev

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.js* ./

EXPOSE 3000

CMD ["npm", "start"]
