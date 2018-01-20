FROM alpine:3.7
COPY ./ccr/requirements.txt /tmp/requirements.txt
COPY ./ccr/ccr.py /tmp/ccr
ENV PATH="${PATH}:/ccr"
RUN  apk update && \
       /sbin/apk add python3 && \
       /bin/mkdir -p /ccr/ccr.d && \
       /usr/bin/python3 -m venv /ccr/ccr.d && \
       source /ccr/ccr.d/bin/activate && \
       pip install -r /tmp/requirements.txt && \
       /bin/mv /tmp/ccr /ccr/ccr && \
       /bin/chmod +x /ccr/ccr && \
       /bin/rm -rf /var/cache/apk/*
