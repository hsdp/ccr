FROM centos:6
COPY ./ccr/* /tmp/
ENV PATH="${PATH}:/ccr"
RUN  /usr/bin/yum -q -y update  && \
       /usr/bin/yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-6.noarch.rpm && \
       /usr/bin/yum -y install python34 && \
       /bin/mkdir -p /ccr/ccr.d && \
       /usr/bin/python3.4 -m venv /ccr/ccr.d && \
       /ccr/ccr.d/bin/pip install -r /tmp/requirements.txt && \
       /bin/mv /tmp/ccr.py /ccr/ccr && \
       /bin/rm -rf /tmp/* && \
       /bin/rm -rf /var/cache/yum && \
       /bin/rm -rf /anaconda-post.log && \
       /bin/rm -rf /root/anaconda-ks.cfg && \
       /bin/chmod +x /ccr/ccr && \
       /bin/mkdir /templates
