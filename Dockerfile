############################################################
# Sample Dockerfile to print hello
# Based on NodeJS and Alpine Linux
# More details https://docs.docker.com/engine/reference/builder/#format
############################################################

# 1. Set a base docker image (see https://hub.docker.com/) and working directory
FROM node:current-alpine

# 2. File Author / Maintainer
MAINTAINER Record Evolution GmbH

# 3. Set the working directory
WORKDIR /root

# 4. Copy settings file or other dependencies
COPY package.json ./

# 5. Update / Install dependencies
RUN apk update && apk add --no-cache git && rm -rf /var/cache/apk/*
RUN npm install

# 6. Bundle app source
COPY . ./

# 7. Expose ports if necessary
EXPOSE 8000:80

# 8. Run the application
CMD [ "npm", "start" ]
