FROM python:3.6.6
ADD requirements.txt /code/
WORKDIR /code
EXPOSE 11317
RUN pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
RUN pip3 install gunicorn -i https://pypi.tuna.tsinghua.edu.cn/simple/
RUN wget https://npm.taobao.org/mirrors/node/v12.13.1/node-v12.13.1-linux-x64.tar.xz && tar xf node-v12.13.1-linux-x64.tar.xz
ENV PATH=$PATH:/code/node-v12.13.1-linux-x64/bin
ENV TZ=Asia/Shanghai
