FROM nginx:alpine
COPY production.conf /etc/nginx/conf.d/default.conf
COPY proxy_locations.conf /etc/nginx/proxy_locations.inc
EXPOSE 80 443 8080
CMD ["nginx", "-g", "daemon off;"]
