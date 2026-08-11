FROM node:20-alpine

WORKDIR /app

ENV NODE_ENV=production

# Copy package files
COPY package*.json ./
COPY .npmrc* ./

# Install dependencies
RUN npm install

# Copy source
COPY . .

# Build
RUN npm run build --workspace=services/api

EXPOSE 3000

CMD ["npm", "start:prod", "--workspace=services/api"]
