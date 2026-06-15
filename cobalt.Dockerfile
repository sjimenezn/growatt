FROM ghcr.io/imputnet/cobalt:11

# Copy cookies file
COPY cookies.json /app/cookies.json

ENV API_ONLY="true"
ENV API_URL="https://genetic-britta-sjimenezn-80e305b4.koyeb.app/"
ENV CORS_WILDCARD="true"
ENV COOKIE_PATH="/app/cookies.json"

EXPOSE 9000
