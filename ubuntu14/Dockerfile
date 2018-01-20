FROM ubuntu:14.04
COPY ./ccr/requirements.txt /tmp/requirements.txt
COPY ./ccr/ccr.py /tmp
ENV PATH="${PATH}:/ccr"
RUN  /usr/bin/apt-get update && \
       /usr/bin/apt-get install -y python3.4-minimal python3.4-venv && \
       /bin/mkdir -p /ccr/ccr.d && \
       /usr/bin/python3.4 -m venv /ccr/ccr.d && \
       /ccr/ccr.d/bin/pip3.4 install -r /tmp/requirements.txt && \
       /bin/mv /tmp/ccr.py /ccr/ccr && \
       /bin/chmod +x /ccr/ccr && \
       /bin/rm -f /tmp/requirements.txt && \
       /usr/bin/apt-get clean
