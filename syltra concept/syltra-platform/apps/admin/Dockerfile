FROM node:20-alpine

WORKDIR /app

ENV NODE_ENV=development

# Copy package files
COPY package*.json ./
COPY .npmrc* ./

# Install (skip postinstall)
RUN npm install --ignore-scripts

# Copy everything
COPY . .

# Build with npm script
RUN npm run admin:build

EXPOSE 3000

CMD ["npm", "run", "admin:start"]
