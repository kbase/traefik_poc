FROM jazzdd/alpine-flask

RUN pip install requests docker && \
    sed -i 's/nginx/root/' /app.ini && \
    sed -i 's/user nginx/user root/' /etc/nginx/nginx.conf

USER root

