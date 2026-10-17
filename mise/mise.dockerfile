FROM fedora:46 AS build

ARG MISE_VERSION

RUN dnf install -y ca-certificates curl tar gzip \
    && dnf clean all
RUN mkdir -p /out/usr/local/bin \
    && curl -fsSL https://mise.run \
        | MISE_VERSION="${MISE_VERSION:+v$MISE_VERSION}" \
          MISE_INSTALL_PATH=/out/usr/local/bin/mise \
          sh

FROM scratch
COPY --from=build /out/usr/local/bin/mise /usr/local/bin/mise
COPY activate-bash.sh /usr/local/share/mise/activate-bash.sh
