FROM python:3.6.6
ADD requirements.txt /code/
WORKDIR /code
EXPOSE 11317
RUN pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
RUN pip3 install gunicorn -i https://pypi.tuna.tsinghua.edu.cn/simple/
ENV TZ=Asia/Shanghai
