FROM node:16 as base-stage

COPY  package.json /code/longue_vue/

WORKDIR /code/longue_vue

RUN npm install

FROM base-stage as production-build-stage

ARG BASE_PATH=/ui/
ARG API_SERVER_HOST="https://localhost/"

COPY . /code/longue_vue/

RUN  sed -i "s,https://dev-langqc.dnapipelines.sanger.ac.uk,${API_SERVER_HOST}/,g" ./src/views/RunView.vue \
  && npm run build -- --base=${BASE_PATH}

FROM httpd:alpine as production

COPY --from=production-build-stage /code/longue_vue/dist/ /usr/local/apache2/htdocs/

FROM base-stage as development

RUN npm install --include=dev

COPY ./vite.config.js /code/longue_vue/vite.config.js
COPY ./index.html /code/longue_vue/index.html

CMD ["npm", "exec", "vite", "--", "--host", "--port", "80", "--base", "/ui/"]
