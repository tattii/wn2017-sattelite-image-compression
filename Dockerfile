FROM python:3.4.3

RUN apt-get update
RUN apt-get install -y python3-numpy python3-scipy python-scikits-learn
RUN pip3 install numpy==1.8.2
