FROM python

RUN pip3 install \
    opcua \
    requests
    # autobahn

    
RUN mkdir /app
COPY . /app
WORKDIR /app

CMD python3 -u opc_ua_client.py
#CMD sleep 10h

