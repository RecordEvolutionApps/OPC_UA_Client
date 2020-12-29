############################################################
# Dockerfile to run OPC UA client
# Based on Linux 
# More details https://docs.docker.com/engine/reference/builder/#format
############################################################

# 1. Set a base docker image (see https://hub.docker.com/) and working directory
FROM mcr.microsoft.com/iotedge/opc-client

# 2. File Author / Maintainer
MAINTAINER Record Evolution GmbH
