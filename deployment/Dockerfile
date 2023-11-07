FROM public.ecr.aws/lambda/python:3.11
CMD bash
WORKDIR /site-packages
RUN pip3.11 install --upgrade pip
RUN pip3.11 install -t . jwcrypto
