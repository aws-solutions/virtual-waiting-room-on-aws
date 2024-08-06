FROM public.ecr.aws/lambda/python:3.12
CMD bash
WORKDIR /site-packages
RUN pip install --upgrade pip
RUN pip install -t . jwcrypto==1.5.6
