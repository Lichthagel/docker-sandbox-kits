FROM alpine:3.24.2

RUN apk add --no-cache bash git curl ca-certificates \
    && addgroup -g 1000 agent \
    && adduser -D -u 1000 -G agent -s /bin/bash -h /home/agent agent \
    && mkdir -p /home/agent/workspace \
    && chown -R agent:agent /home/agent

USER agent
WORKDIR /home/agent/workspace
ENTRYPOINT ["bash"]
CMD []
