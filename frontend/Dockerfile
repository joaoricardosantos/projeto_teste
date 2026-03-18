FROM node:20-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install && npm install vite --save-dev

COPY . .

EXPOSE 3000

CMD ["./node_modules/.bin/vite", "--host", "0.0.0.0", "--port", "3000"]