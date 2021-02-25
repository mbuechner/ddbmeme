FROM python:3.9
MAINTAINER Michael Büchner <m.buechner@dnb.de>
RUN git clone https://github.com/jacebrowning/memegen.git /home/memegen
WORKDIR /home/memegen
# no tags, no versions, so we need to use commit hash :-(
RUN git checkout e97e959
RUN python3 -m pip install pipenv poetry uvicorn gunicorn uvloop
RUN { \
	echo "WEB_CONCURRENCY=2"; \
	echo "MAX_REQUESTS=0"; \
	echo "MAX_REQUESTS_JITTER=0"; \
	echo "WATERMARK_OPTIONS=blank,DDBmeme"; \
	} > .env
RUN export PIPENV_VENV_IN_PROJECT="enabled"
RUN pipenv install
RUN pipenv run poetry install

COPY DDBmeme/ /home/DDBmeme/
WORKDIR /home/DDBmeme
RUN pipenv install --ignore-pipfile

CMD ["/home/DDBmeme/run.sh"]

EXPOSE 8080
