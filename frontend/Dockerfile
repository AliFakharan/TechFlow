# TechFlow frontend — Vite dev server (proxies /api to Django backend).
# For production you can build with `vite build` and serve dist/ from Django;
# the compose setup mirrors the documented dev flow (dev server on 5173).
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install --no-audit --no-fund

COPY . .

ENV VITE_PROXY_TARGET=http://backend:8000
EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
