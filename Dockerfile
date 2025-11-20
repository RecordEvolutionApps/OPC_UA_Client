FROM python:3.13-slim

WORKDIR /usr/src/app

# (optional) use python wheels from piwheels.org (speeds up build time for arm architectures)
# RUN echo '[global]' > /etc/pip.conf && echo 'extra-index-url=https://www.piwheels.org/simple' >> /etc/pip.conf

RUN pip install --upgrade pip

# Copy project configuration files
COPY pyproject.toml ./

# Install dependencies from pyproject.toml
RUN pip install .

# Copy application code
COPY *.py ./

CMD python3 -u main.py


