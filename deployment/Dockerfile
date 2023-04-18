FROM public.ecr.aws/amazonlinux/amazonlinux:2
CMD bash
RUN mkdir -p site-packages/
RUN amazon-linux-extras enable python3.8
RUN yum install -y python3.8
RUN pip3.8 install pip --upgrade
RUN pip install -t site-packages/ jwcrypto
