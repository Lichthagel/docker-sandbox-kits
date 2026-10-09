FROM alpine:3.24.2

RUN apk add --no-cache bash git git-daemon curl ca-certificates doas \
    libstdc++ docker docker-cli-compose tini-static \
    && printf '%s\n' 'permit nopass agent as root' > /etc/doas.conf \
    && chmod 0400 /etc/doas.conf \
    && addgroup -S -g 1000 agent \
    && adduser -D -u 1000 -G agent -s /bin/bash -h /home/agent agent \
    && addgroup agent docker \
    && mkdir -p /home/agent/workspace \
    && chown -R agent:agent /home/agent

COPY --chown=agent:agent mise-config.toml /home/agent/.config/mise/config.toml
COPY --chown=agent:agent bashrc /home/agent/.bashrc

RUN touch /etc/sandbox-persistent.sh \
    && chown agent:agent /etc/sandbox-persistent.sh \
    && chmod 0644 /etc/sandbox-persistent.sh \
    && printf '%s\n' '. /etc/sandbox-persistent.sh' \
        > /etc/profile.d/sandbox-persistent.sh \
    && printf '%s\n' '. /etc/sandbox-persistent.sh' >> /home/agent/.bashrc

LABEL com.docker.sandboxes.start-docker="true"

ENV HOME=/home/agent \
    PATH="/home/agent/.local/bin:${PATH}" \
    BASH_ENV=/etc/sandbox-persistent.sh \
    NO_PROXY=localhost,127.0.0.1,::1,172.17.0.0/16 \
    no_proxy=localhost,127.0.0.1,::1,172.17.0.0/16

USER agent
WORKDIR /home/agent/workspace
ENTRYPOINT ["/sbin/tini-static", "-s", "--"]
CMD ["bash"]
