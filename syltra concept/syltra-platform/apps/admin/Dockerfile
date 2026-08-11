FROM node:20-alpine

WORKDIR /app

ENV NODE_ENV=development

# Copy package files
COPY package*.json ./
COPY .npmrc* ./

# Install dependencies
RUN npm install

# Copy project
COPY . .

# Build
RUN npm run build --workspace=@syltra/admin

EXPOSE 3000

CMD ["npm", "start", "--workspace=@syltra/admin"]
