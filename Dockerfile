from ubuntu:latest

RUN apt-get update 
RUN apt-get install libavdevice-dev libavfilter-dev libopus-dev libvpx-dev pkg-config libsrtp2-dev python3-dev python3-pip -y

WORKDIR /env
COPY ./requirements.txt ./env/requirements.txt
RUN pip3 install -r ./env/requirements.txt
COPY . /env
