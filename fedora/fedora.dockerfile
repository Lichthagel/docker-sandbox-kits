FROM fedora:44

RUN dnf install -y bash ca-certificates curl docker-buildx docker-cli \
        docker-compose git git-daemon iptables-nft libstdc++ moby-engine sudo tini-static \
    && dnf clean all \
    && (getent group docker >/dev/null || groupadd --system docker)

RUN alternatives --set iptables /usr/sbin/iptables-nft

RUN groupadd --gid 1000 agent \
    && useradd --uid 1000 --gid agent --groups docker \
        --create-home --home-dir /home/agent --shell /bin/bash agent \
    && mkdir -p /home/agent/workspace \
    && chown -R agent:agent /home/agent \
    && printf '%s\n' 'agent ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/agent \
    && chmod 0440 /etc/sudoers.d/agent

RUN mkdir -p /etc/docker/certs.d/docker.io

COPY docker-registry-ca.sh /usr/local/sbin/docker-registry-ca

RUN mkdir -p /usr/local/share/fedora-kit \
    && install -m 0755 /usr/local/sbin/docker-registry-ca \
        /usr/local/share/fedora-kit/docker-registry-ca.sh

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
ENTRYPOINT ["/usr/bin/tini-static", "-s", "--"]
CMD ["bash"]
