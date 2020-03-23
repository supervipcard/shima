FROM python:3.6.6
ADD requirements.txt /code/
WORKDIR /code
EXPOSE 11317
RUN pip3 install -r requirements.txt
RUN pip3 install gunicorn
ENV TZ=Asia/Shanghai
CMD gunicorn --config gunicorn_config.py shima.wsgi:application
