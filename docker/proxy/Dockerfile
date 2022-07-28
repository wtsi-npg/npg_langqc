FROM ubuntu:focal

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update -qq\
  && apt-get install -qq apache2 libapache2-mod-auth-openidc
  
COPY 000-default.conf /etc/apache2/sites-enabled/000-default.conf

RUN a2enmod proxy\
  && a2enmod proxy_http\
  && a2enmod proxy_ajp\
  && a2enmod rewrite\
  && a2enmod deflate\
  && a2enmod headers\
  && a2enmod proxy_balancer\
  && a2enmod proxy_connect\
  && a2enmod proxy_html \
  && a2enmod ssl 

CMD apachectl -D FOREGROUND
