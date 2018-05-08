FROM python:3.6
RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/v1.9.0/bin/linux/amd64/kubectl
RUN mv ./kubectl /usr/local/bin/kubectl && chmod +x /usr/local/bin/kubectl
ADD . /experiments
WORKDIR /experiments
RUN make deps && make lint
CMD ["python3"]
