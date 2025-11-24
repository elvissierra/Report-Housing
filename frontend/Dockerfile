FROM node:20-alpine

WORKDIR /app

# Install deps
COPY package.json ./
RUN npm install

# Copy the rest of the frontend
COPY . .

EXPOSE 8080

# Vite
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "8080"]