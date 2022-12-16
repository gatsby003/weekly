FROM python

WORKDIR /code

COPY . .

RUN pip3 install -r requirements.txt

VOLUME . . 

ENV FLASK_APP=spotify-etl.py 

CMD [ "python3", "-m" , "flask", "run"]
