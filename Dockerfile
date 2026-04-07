FROM ubuntu:26.04

# setup
ENV TERM=xterm-256color
ENV LANG=C.UTF-8
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt -y update && apt -y upgrade
RUN apt -y install unminimize
RUN yes | unminimize

## install dependencies
RUN apt -y install gdal-bin libjxl-tools python3-venv

# copy all python files into container
COPY *.py /app/

# python virtual environment
WORKDIR /app
RUN python3 -m venv .venv
RUN .venv/bin/pip install boto3 datetime matplotlib pillow pillow-jxl-plugin polar2grid scipy tqdm
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# image defaults
WORKDIR /app
