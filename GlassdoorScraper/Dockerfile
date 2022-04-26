# syntax=docker/dockerfile:1
FROM selenium/standalone-chrome
LABEL description="Glassdoor Scraper"

USER root
RUN apt-get -y update
RUN apt-get install -y software-properties-common
RUN apt-get install -y libmysqlclient-dev
RUN apt-add-repository -y universe
RUN apt-get install -y python3-pip

ARG INSTALL_DIR=/GlassdoorScraper
COPY . $INSTALL_DIR
WORKDIR $INSTALL_DIR
RUN pip3 install -r requirements.txt
ENV FLASK_APP=app
ENV FLASK_RUN_HOST=0.0.0.0
EXPOSE 5000

CMD ["flask", "run"]