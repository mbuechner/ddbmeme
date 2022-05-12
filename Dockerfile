FROM python:3.10-alpine
MAINTAINER Michael Büchner <m.buechner@dnb.de>
ARG MEMEGEN_GIT_HASH=afefed2952658d9d2da78489aed493d964103400
RUN apk add \
		openjpeg \
		libimagequant \
		libjpeg-turbo \
		libxcb \
		tiff \
		supervisor && \
	apk add --no-cache --virtual .build-deps  \
		bluez-dev \
		bzip2-dev \
		coreutils \
		fish \
		dpkg-dev dpkg \
		expat-dev \
		findutils \
		freetype-dev \
		fribidi-dev \
		g++ \
		gcc \
		git \
		gdbm-dev \
		harfbuzz-dev \
		jpeg-dev \
		lcms2-dev \
		libapparmor \
		libc-dev \
		libffi-dev \
		libimagequant-dev \
		libnsl-dev \
		libpng-dev \
		libtirpc-dev \
		libwebp-dev \
		libxcb-dev \
		linux-headers \
		make \
		ncurses-dev \
		openjpeg-dev \
		openssl-dev \
		pax-utils \
		readline-dev \
		sqlite-dev \
		tcl-dev \
		tiff-dev \
		tk \
		tk-dev \
		util-linux-dev \
		xz-dev \
		zlib-dev && \
	wget -O /home/memegen.zip https://github.com/jacebrowning/memegen/archive/$MEMEGEN_GIT_HASH.zip && \
	unzip /home/memegen.zip -d /home && \
	mv /home/memegen-$MEMEGEN_GIT_HASH/ /home/memegen/ && \
	rm -f /home/memegen.zip;

WORKDIR /home/memegen

ENV PIPENV_VENV_IN_PROJECT="enabled"
ENV RUN_USER nobody
ENV RUN_GROUP 0

RUN chown -R ${RUN_USER}:${RUN_GROUP} . && \
	python3 -m pip install --no-cache --upgrade pip pipenv poetry && \
	{ \
		echo "WEB_CONCURRENCY=2"; \
		echo "MAX_REQUESTS=0"; \
		echo "MAX_REQUESTS_JITTER=0"; \
		echo "WATERMARK_OPTIONS=blank,DDBmeme"; \
	} > .env && \
	pipenv install && \
	pipenv run poetry install;

# add supervisord config
COPY --chown=${RUN_USER}:${RUN_GROUP} config/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# add DDBmeme and build it
COPY --chown=${RUN_USER}:${RUN_GROUP} DDBmeme/ /home/ddbmeme/
WORKDIR /home/ddbmeme
RUN pipenv install && \
	apk del --no-network .build-deps && \
	touch /run/supervisord.pid && chgrp -R ${RUN_GROUP} /run/supervisord.pid && chmod -R g=u /run/supervisord.pid;

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
EXPOSE 8080
