FROM python:3

ADD flair_removal.py /
ADD requirements.txt /
ADD puni /puni/

RUN pip install -r requirements.txt

CMD [ "python", "./flair_removal.py" ]