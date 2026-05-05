FROM node:20-alpine

WORKDIR /app

COPY web-ui/infrastructure/adapters/frontend/package*.json ./
RUN npm ci

COPY web-ui/infrastructure/adapters/frontend/ ./

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
