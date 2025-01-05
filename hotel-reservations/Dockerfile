FROM ubuntu:22.04

RUN apt-get update && apt-get install -y rsyslog && rm -rf /var/lib/apt/lists/*

RUN sed -i 's/#module(load="imudp")/module(load="imudp")/' /etc/rsyslog.conf && \
    sed -i 's/#input(type="imudp" port="514")/input(type="imudp" port="514")/' /etc/rsyslog.conf && \
    sed -i 's/#module(load="imtcp")/module(load="imtcp")/' /etc/rsyslog.conf && \
    sed -i 's/#input(type="imtcp" port="514")/input(type="imtcp" port="514")/' /etc/rsyslog.conf

EXPOSE 514/udp
EXPOSE 514/tcp

CMD ["rsyslogd", "-n"]
