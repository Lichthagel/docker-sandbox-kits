ARG MISE_LIBC=glibc

FROM alpine:3.24.2 AS build-musl

ARG MISE_VERSION

RUN apk add --no-cache ca-certificates curl
RUN mkdir -p /out/usr/local/bin \
    && curl -fsSL https://mise.run \
        | MISE_VERSION="${MISE_VERSION:+v$MISE_VERSION}" \
          MISE_INSTALL_PATH=/out/usr/local/bin/mise \
          sh

FROM fedora:44 AS build-glibc

ARG MISE_VERSION

RUN dnf install -y ca-certificates curl tar gzip \
    && dnf clean all
RUN mkdir -p /out/usr/local/bin \
    && curl -fsSL https://mise.run \
        | MISE_VERSION="${MISE_VERSION:+v$MISE_VERSION}" \
          MISE_INSTALL_PATH=/out/usr/local/bin/mise \
          sh

ARG MISE_LIBC
FROM build-${MISE_LIBC} AS selected
FROM scratch
COPY --from=selected /out/usr/local/bin/mise /usr/local/bin/mise
COPY activate-bash.sh /usr/local/share/mise/activate-bash.sh
