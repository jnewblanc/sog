# Install the base requirements for the app.
# This stage is to support development.
FROM python:3.8 AS base
LABEL sog_version="0.1"
# Set up environment vars
ENV SOG_SERVER_DIR: "/opt/sog"
ENV SOG_SERVER_APP: "server.py"
ENV SOG_SERVER_PORT: "8888"
# ENV SOG_SERVER_TZ: "America/Los_Angeles"
# ENV SOG_SERVER_DATADIR: "/opt/sog/.data"
# ENV SOG_SERVER_LOGDIR: "/opt/sog/.logs"
# ENV SOG_SERVER_HOST: "127.0.0.1"
# Adjust timeZone
RUN cp -f /usr/share/zoneinfo/America/Los_Angeles /etc/localtime
# Install requirements
COPY requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt
# Copy code to container - for now, we use a mounted volume
#COPY . /opt/sog
# EXPOSE 8888
EXPOSE ${SOG_SERVER_PORT}
#CMD [ "python", "${SOG_SERVER_DIR}/${SOG_SERVER_APP}" ]
CMD [ "python", "/opt/sog/server.py" ]
