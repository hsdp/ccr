FROM alpine:3.10.3
COPY ./ccr/requirements.txt /tmp/requirements.txt
COPY ./ccr/* /tmp/
ENV PATH="${PATH}:/ccr"
RUN  apk update && \
       /sbin/apk add python3 && \
       /bin/mkdir -p /ccr/ccr.d && \
       /usr/bin/python3 -m venv /ccr/ccr.d && \
       /ccr/ccr.d/bin/pip install -r /tmp/requirements.txt && \
       /bin/mv /tmp/ccr.py /ccr/ccr && \
       /bin/chmod +x /ccr/ccr && \
       /bin/rm -rf /tmp/* && \
       /bin/rm -rf /var/cache/apk/*
