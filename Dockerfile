FROM python:3.7-stretch

MAINTAINER m.buechner@dnb.de

RUN apt-get install -y git
RUN git clone https://github.com/jacebrowning/memegen.git /home/memegen
RUN apt-get purge -y git
WORKDIR /home/memegen
RUN python3.7 -m pip install pipenv
RUN { \
	echo "FLASK_ENV=production"; \
	echo "GOOGLE_ANALYTICS_TID=local"; \
	echo "#REGENERATE_IMAGES=true"; \
	echo "WATERMARK_OPTIONS=DDBmeme"; \
	} > .env
RUN python3.7 -m pipenv install --ignore-pipfile
RUN make install

COPY DDBmeme/ /home/DDBmeme/
WORKDIR /home/DDBmeme
RUN python3.7 -m pipenv install --ignore-pipfile

CMD ["/home/DDBmeme/run.sh"]

EXPOSE 80
