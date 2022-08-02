FROM ubuntu:focal

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update -qq \
  && apt-get install -qq  --no-install-recommends apache2 libapache2-mod-auth-openidc ca-certificates \
  && rm -rf /var/lib/apt/lists/*

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
  && a2enmod ssl \
  # Redirect logs to stdout/stderr for easier docker logging.
  && ln -sf /dev/stdout /var/log/apache2/access.log \
  && ln -sf /dev/stdout /var/log/apache2/other_vhosts_access.log \
  && ln -sf /dev/stderr /var/log/apache2/error.log

CMD ["apachectl", "-D", "FOREGROUND"]
