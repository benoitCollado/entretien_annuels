# syntax=docker/dockerfile:1
FROM node:22-alpine AS base
WORKDIR /app

FROM base AS deps
COPY package.json package-lock.json* ./
RUN npm ci


FROM base AS dev
COPY --from=deps /app/node_modules ./node_modules
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

FROM base AS build
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build


FROM nginx:1.27-alpine AS prod
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
# 127.0.0.1 et non « localhost » : dans l'image Alpine, localhost résout en ::1
# et la sonde échouerait si nginx n'écoutait qu'en IPv4.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
CMD ["nginx", "-g", "daemon off;"]
