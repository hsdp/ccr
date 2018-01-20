FROM centos:7
COPY ./ccr/requirements.txt /tmp/requirements.txt
COPY ./ccr/ccr.py /tmp
ENV PATH="${PATH}:/ccr"
RUN  /usr/bin/yum -q -y update  && \
       /usr/bin/yum -y install https://centos7.iuscommunity.org/ius-release.rpm && \
       /usr/bin/yum -y install python36u python36u-pip && \
       /usr/bin/mkdir -p /ccr/ccr.d && \
       /usr/bin/python3.6 -m venv /ccr/ccr.d && \
       source /ccr/ccr.d/bin/activate && \
       pip install -r /tmp/requirements.txt && \
       /bin/mv /tmp/ccr.py /ccr/ccr && \
       /bin/rm -rf /tmp/requirements.txt && \
       /bin/rm -rf /var/cache/yum && \
       /bin/rm -rf /anaconda-post.log && \
       /bin/rm -rf /root/anaconda-ks.cfg && \
       /bin/chmod +x /ccr/ccr && \
       /usr/bin/mkdir /templates
