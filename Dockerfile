FROM python:3.7-stretch

MAINTAINER m.buechner@dnb.de

COPY DDBmeme/ /home/DDBmeme/

RUN apt-get install git
RUN git clone https://github.com/jacebrowning/memegen.git /home/memegen
RUN python3.7 -m pip install pipenv
WORKDIR /home/memegen
RUN echo "FLASK_ENV=production" >> .env
RUN echo "GOOGLE_ANALYTICS_TID=local" >> .env
RUN echo "#REGENERATE_IMAGES=true" >> .env
RUN echo "WATERMARK_OPTIONS=DDBmeme" >> .env
RUN python3.7 -m pipenv install --system --deploy --ignore-pipfile
RUN make install
RUN python3.7 -m pipenv run pip install python-dotenv
WORKDIR /home/DDBmeme
RUN python3.7 -m pipenv install --system --deploy --ignore-pipfile

CMD ["/home/DDBmeme/run.sh"]

EXPOSE 80
