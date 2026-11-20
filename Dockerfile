FROM python:3.13-alpine AS runtime-base

RUN apk add --no-cache \
    curl \
    freetype \
    fribidi \
    harfbuzz \
    lcms2 \
    libimagequant \
    libjpeg-turbo \
    libstdc++ \
    libwebp-tools \
    libxcb \
    openjpeg \
    tiff

FROM runtime-base AS build

ARG MEMEGEN_GIT_HASH=b38d4ad067308f467d8a981a9cd9a2277d388930
ARG SOURCE_DATE_EPOCH
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true

RUN apk add --no-cache \
    build-base \
    cmake \
    freetype-dev \
    fribidi-dev \
    git \
    harfbuzz-dev \
    lcms2-dev \
    libffi-dev \
    libimagequant-dev \
    libjpeg-turbo-dev \
    libpng-dev \
    libwebp-dev \
    libxcb-dev \
    linux-headers \
    openjpeg-dev \
    tiff-dev \
    zlib-dev \
    && python -m pip install --no-cache-dir 'poetry==2.5.1' 'cyclonedx-bom==9.0.0'

WORKDIR /home/memegen
RUN curl --fail --location --retry 3 --output /tmp/memegen.tar.gz \
        "https://github.com/jacebrowning/memegen/archive/${MEMEGEN_GIT_HASH}.tar.gz" \
    && tar -xzf /tmp/memegen.tar.gz --strip-components=1 \
    && sed -i 's/Memegen.link/DDBmeme/g' app/settings.py \
    && poetry install --only main

WORKDIR /home/ddbmeme
COPY DDBmeme/requirements.txt ./
RUN python -m venv /opt/ddbmeme-venv \
    && /opt/ddbmeme-venv/bin/python -m pip install --no-cache-dir -r requirements.txt 'supervisor==4.3.0'

COPY DDBmeme/ ./
RUN /opt/ddbmeme-venv/bin/python manage.py check \
    && cyclonedx-py environment /opt/ddbmeme-venv --output-reproducible --spec-version 1.6 \
        --output-file sbom.cdx.json

FROM runtime-base
LABEL maintainer="Michael Büchner <m.buechner@dnb.de>"

ENV PATH="/opt/ddbmeme-venv/bin:${PATH}" \
    HOME=/tmp \
    TMPDIR=/tmp \
    PYTHONDONTWRITEBYTECODE=1
COPY --from=build /home/memegen /home/memegen
COPY --from=build /home/ddbmeme /home/ddbmeme
COPY --from=build /opt/ddbmeme-venv /opt/ddbmeme-venv
COPY config/supervisord.conf config/ddbmeme-start.sh config/exit-on-fatal.py /etc/supervisor/

# Memegen writes generated files and its template cache as the OpenShift UID.
RUN mkdir -p /home/memegen/images \
    && chmod -R g=u /home/memegen/images /home/memegen/templates

WORKDIR /home/ddbmeme
USER 65534:0
EXPOSE 8080
CMD ["/opt/ddbmeme-venv/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
