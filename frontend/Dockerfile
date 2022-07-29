FROM node:16 as build-stage

ARG BASE_PATH=/ui/
ARG API_SERVER_HOST="https://localhost/"

COPY  package.json /code/longue_vue/

WORKDIR /code/longue_vue

RUN npm install

COPY . /code/longue_vue/

RUN  sed -i "s,https://dev-langqc.dnapipelines.sanger.ac.uk,${API_SERVER_HOST}/,g" ./src/views/RunView.vue \
  && npm run build -- --base=${BASE_PATH}

FROM httpd:alpine

COPY --from=build-stage /code/longue_vue/dist/ /usr/local/apache2/htdocs/
