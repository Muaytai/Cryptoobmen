FROM node:22.15.0

WORKDIR /usr/src/app

RUN npm install -g npm@latest

COPY package*.json ./
RUN npm cache clean --force
RUN npm install
