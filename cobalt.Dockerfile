FROM ghcr.io/imputnet/cobalt:11

ENV API_ONLY="true"
ENV API_URL="https://genetic-britta-sjimenezn-80e305b4.koyeb.app/"
ENV CORS_WILDCARD="true"

EXPOSE 9000
