# Frontend build
FROM node:18 AS builder
WORKDIR /app
COPY . .
RUN npm install && npm run build
# Host the build
FROM nginx:alpine
COPY --from=builder /app/build/ /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/nginx.conf.template
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
EXPOSE 80