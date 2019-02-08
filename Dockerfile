FROM python:3.6-alpine

MAINTAINER m.buechner@dnb.de

COPY DDBmeme/ /home/DDBmeme/

RUN apk add --no-cache --virtual .build-deps git gcc make build-base bash jpeg-dev zlib-dev tiff-dev freetype-dev lcms2-dev tk-dev tcl-dev openjpeg-dev
RUN git clone https://github.com/jacebrowning/memegen.git /home/memegen
RUN pip install pipenv
WORKDIR /home/memegen
RUN echo "FLASK_ENV=production" >> .env
RUN echo "GOOGLE_ANALYTICS_TID=local" >> .env
RUN echo "#REGENERATE_IMAGES=true" >> .env
RUN echo "WATERMARK_OPTIONS=DDBmeme" >> .env
RUN pipenv install --system --deploy --ignore-pipfile
RUN make install
RUN pipenv run pip install python-dotenv
WORKDIR /home/DDBmeme
RUN pipenv install --system --deploy --ignore-pipfile

CMD ["/home/DDBmeme/run.sh"]

EXPOSE 80