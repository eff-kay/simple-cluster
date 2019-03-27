FROM ubuntu
RUN apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    net-tools \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*
RUN apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    netcat \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*