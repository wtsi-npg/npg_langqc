FROM node:18-alpine as base-stage

COPY  package.json /code/longue_vue/

WORKDIR /code/longue_vue

RUN npm install

FROM base-stage as production-build-stage

ARG BASE_PATH=/ui/

COPY . /code/longue_vue/

RUN npm run build -- --base=${BASE_PATH}

FROM httpd:alpine as production

COPY --from=production-build-stage /code/longue_vue/dist/ /usr/local/apache2/htdocs/
COPY ./httpd.conf /usr/local/apache2/conf/httpd.conf

FROM base-stage as development

RUN npm install --include=dev

COPY ./vite.config.js /code/longue_vue/vite.config.js
COPY ./index.html /code/longue_vue/index.html

CMD ["npm", "exec", "vite", "--", "--host", "--port", "80", "--base", "/ui/"]
