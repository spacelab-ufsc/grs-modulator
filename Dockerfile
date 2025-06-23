FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    UHD_IMAGES_DIR=/usr/share/uhd/images \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    uhd-host \
    libuhd-dev \
    python3 \
    python3-uhd \
    python3-pip \
    python3-setuptools \
    ca-certificates \
    wget \
    libiio-dev \
    libad9361-dev \
    usbutils \
    && rm -rf /var/lib/apt/lists/*

RUN uhd_images_downloader

WORKDIR /app

COPY setup.py .
COPY setup.cfg .
COPY README.md .
COPY grs_modulator/ ./grs_modulator/

RUN python3 setup.py install

ENTRYPOINT ["grs-modulator"]

CMD ["--help"]

