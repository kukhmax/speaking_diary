# Dockerfile для Frontend
# Stage 1: Build React app
FROM node:18-alpine AS build

WORKDIR /app

# Копирование package files
COPY package*.json ./

# Установка зависимостей
RUN npm install --silent

# Копирование исходного кода
COPY . .

# Проброс переменных окружения во время сборки
ARG REACT_APP_API_URL=/api
ARG REACT_APP_VERSION
ENV REACT_APP_API_URL=${REACT_APP_API_URL}
ENV REACT_APP_VERSION=${REACT_APP_VERSION}

# Build приложения
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Копирование build файлов
COPY --from=build /app/build /usr/share/nginx/html

# Копирование конфигурации Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Открытие порта
EXPOSE 80

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Запуск Nginx
CMD ["nginx", "-g", "daemon off;"]