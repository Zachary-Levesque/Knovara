# Frontend container image definition.
#
# This file will define the local development image for the Next.js frontend,
# install Node dependencies, set the working directory, and provide the runtime
# command used by Docker Compose.
FROM node:22-alpine

WORKDIR /app

COPY package.json .
RUN npm install

COPY . .

CMD ["npm", "run", "dev"]

