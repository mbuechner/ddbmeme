FROM python:3-buster
MAINTAINER Michael Büchner <m.buechner@dnb.de>
RUN apt-get update && apt-get install -y python3-dev
RUN git clone https://github.com/jacebrowning/memegen.git /home/memegen
WORKDIR /home/memegen
RUN python3 -m pip install pipenv
RUN { \
	echo "FLASK_ENV=production"; \
	echo "GOOGLE_ANALYTICS_TID=local"; \
	echo "#REGENERATE_IMAGES=true"; \
	echo "WATERMARK_OPTIONS=DDBmeme"; \
	} > .env
RUN python3 -m pipenv install --ignore-pipfile
RUN make install
COPY DDBmeme/ /home/DDBmeme/
WORKDIR /home/DDBmeme
RUN python3 -m pipenv install --ignore-pipfile
CMD ["/home/DDBmeme/run.sh"]
EXPOSE 80

