FROM alpine:3.24.2 AS build

ARG MISE_VERSION

RUN apk add --no-cache ca-certificates curl
RUN mkdir -p /out/usr/local/bin \
    && curl -fsSL https://mise.run \
        | MISE_INSTALL_MUSL=1 \
          MISE_VERSION="${MISE_VERSION:+v$MISE_VERSION}" \
          MISE_INSTALL_PATH=/out/usr/local/bin/mise \
          sh

FROM scratch
COPY --from=build /out/usr/local/bin/mise /usr/local/bin/mise
