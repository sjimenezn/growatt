FROM ghcr.io/imputnet/cobalt:11

# Install bash and curl for better console experience
RUN apk add --no-cache bash curl

ENV API_ONLY="true"
ENV API_URL="https://genetic-britta-sjimenezn-80e305b4.koyeb.app/"
ENV CORS_WILDCARD="true"

EXPOSE 9000

# Use bash as default shell
SHELL ["/bin/bash", "-c"]
