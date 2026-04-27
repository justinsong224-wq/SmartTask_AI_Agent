FROM node:20-slim

WORKDIR /app

# 不在容器里 npm install，直接用本地已装好的 node_modules
COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]