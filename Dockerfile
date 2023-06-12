FROM python:3.9

WORKDIR /usr/src/app

# (optional) use python wheels from piwheels.org (speeds up build time for arm architectures)
# RUN echo '[global]' > /etc/pip.conf && echo 'extra-index-url=https://www.piwheels.org/simple' >> /etc/pip.conf

RUN pip install --upgrade pip

# install rust for building cryptography
RUN curl https://sh.rustup.rs -sSf | bash -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY opc_ua_client.py ./

CMD python3 -u opc_ua_client.py


