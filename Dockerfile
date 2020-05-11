FROM python:3.7-slim as base

FROM base as builder

RUN apt-get update 
RUN apt-get install libavdevice-dev libavfilter-dev libopus-dev libvpx-dev pkg-config libsrtp2-dev python3.7-dev python3-pip -y

WORKDIR /env
COPY ./requirements.txt ./env/requirements.txt
RUN pip3 install --user -r ./env/requirements.txt

FROM python:3.7-slim as worker

COPY --from=builder root/.local root/.local
COPY . /worker
WORKDIR /worker
