# node-server/Dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package.json first for better caching
COPY package.json ./

# Install dependencies (this will generate node_modules)
RUN npm install --production

# Copy application code
COPY server.js .

EXPOSE 3000

CMD ["node", "server.js"]
