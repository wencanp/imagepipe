# Frontend build
FROM node:18 AS builder
WORKDIR /app
COPY . .
RUN npm install && npm run build
# Host the build
FROM nginx:alpine
COPY build/ /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
CMD ["nginx", "-g", "daemon off;"]
