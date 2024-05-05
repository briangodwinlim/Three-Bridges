FROM python:3.9

WORKDIR /
COPY . .

RUN apt update && apt -y upgrade
RUN apt install -y python3 python3-pip pkg-config
RUN python3 -m pip install --upgrade pip
RUN pip3 install -r requirements.txt
