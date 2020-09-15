# Install the base requirements for the app.
# This stage is to support development.
FROM python:3.8 AS base
LABEL sog_version="0.1"
# Set up environment vars
ENV SOG_SERVER_DIR: /opt/sog
ENV SOG_SERVER_APP: server.py
# install requirements
RUN cp -f /usr/share/zoneinfo/America/Los_Angeles /etc/localtime
COPY requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt
# Copy code to container - for now, we use a mounted volume
#COPY . /opt/sog
EXPOSE 8888
CMD [ "python", "{SOG_SERVER_DIR}/{SOG_SERVER_APP}" ]
