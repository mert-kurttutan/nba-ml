# VERSION 1.10
# AUTHOR: Mert Kurttutan
# BUILD: docker build --rm -t amazon/mwaa-local .

FROM public.ecr.aws/amazonlinux/amazonlinux:2
LABEL maintainer="amazon"

# User settings
ARG MLFLOW_USER_HOME=/usr/local/mlflow
ARG PYTHON_DEPS=""
ARG SYSTEM_DEPS=""
ARG INDEX_URL=""
ENV MLFLOW_HOME=${MLFLOW_USER_HOME}


COPY script/bootstrap.sh /bootstrap.sh
COPY script/systemlibs.sh /systemlibs.sh
COPY ./requirements.txt /requirements.txt
COPY ./nbaetl /nbaetl
COPY script/aws_config.sh /aws_config.sh

RUN chmod u+x /systemlibs.sh && /systemlibs.sh
RUN chmod u+x /bootstrap.sh && /bootstrap.sh
RUN chmod +x /aws_config.sh

# Post bootstrap to avoid expensive docker rebuilds
COPY script/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

EXPOSE 8080 5555 8793


USER mlflow
WORKDIR ${MLFLOW_USER_HOME}
#ENTRYPOINT ["/entrypoint.sh"]
