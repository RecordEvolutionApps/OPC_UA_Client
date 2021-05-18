############################################################
# Dockerfile to run OPC UA server
# Based on Linux 
# More details https://docs.docker.com/engine/reference/builder/#format
############################################################

# 1. Set a base docker image (see https://hub.docker.com/) and working directory
FROM raspbian/stretch

# 2. File Author / Maintainer
MAINTAINER Record Evolution GmbH

RUN apt-get update && apt-get install -y \
    python3-pip \
    git \
    libffi-dev \
    libzbar-dev \
    clang \
    python3-dev \
    libssl-dev \
    build-essential \
    scons \
    swig \
    libxml2-dev \ 
    libxslt-dev \ 
    libraspberrypi-bin \ 
    i2c-tools \  
    python-smbus

RUN pip3 install pytz \
    python-dateutil \
    lxml \
    pyserial \
    requests \
    autobahn \
    twisted \
    pyserial \
    cbor

RUN git clone https://github.com/FreeOpcUa/python-opcua.git
RUN cd python-opcua && python3 setup.py build && python3 setup.py install 
    
RUN mkdir /app
COPY . /app
WORKDIR /app

CMD python3 -u opc_ua_client.py
#CMD sleep 10h

