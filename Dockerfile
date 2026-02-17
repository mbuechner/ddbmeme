FROM python:3.13-alpine
LABEL maintainer="Michael Büchner <m.buechner@dnb.de>"
ARG MEMEGEN_GIT_HASH=a30ce9e5de7dd36d7c9a41336bc7fe319ab4a196
RUN apk add \
		curl \
		freetype-dev \
		jpeg-dev \
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
		fribidi-dev \
		g++ \
		gcc \
		git \
		gdbm-dev \
		harfbuzz-dev \
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
	sed -i 's/Memegen.link/DDBmeme/g' /home/memegen/app/settings.py && \
	rm -f /home/memegen.zip;

WORKDIR /home/memegen

ENV PIPENV_VENV_IN_PROJECT="enabled"
ENV POETRY_VIRTUALENVS_CREATE=false
ENV RUN_USER=nobody
ENV RUN_GROUP=65534

RUN chown -R ${RUN_USER}:${RUN_GROUP} . && \
	python3 -m pip install --no-cache-dir poetry && \
	poetry install --only=main;

# add DDBmeme and build it
COPY --chown=${RUN_USER}:${RUN_GROUP} DDBmeme/ /home/ddbmeme/
WORKDIR /home/ddbmeme
RUN python3 -m pip install --no-cache-dir -r requirements.txt && \
	python3 manage.py migrate;

# add supervisord config
COPY --chown=${RUN_USER}:${RUN_GROUP} config/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN apk del --no-network .build-deps && \
	touch /run/supervisord.pid && chown ${RUN_USER}:${RUN_USER} /run/supervisord.pid && chmod 664 /run/supervisord.pid;

# Run supervisord as nobody
USER ${RUN_USER}
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
EXPOSE 8080
