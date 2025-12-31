# ===============================
# FRONTEND BUILD STAGE
# ===============================
FROM node:20-bullseye-slim AS build

WORKDIR /app

# sadece dependency bilgileri
COPY package.json package-lock.json ./
RUN npm ci

# kaynak kod
COPY . .
RUN npm run build

# ===============================
# FRONTEND RUNTIME
# ===============================
FROM nginx:alpine

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
