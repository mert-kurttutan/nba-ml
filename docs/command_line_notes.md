# Shell commands used frequently

Built docker image

```Bash
 sudo docker build --tag nba-mlflow-dag:latest .
```

For interactive runtime of docker container, through bash

```Bash
 sudo docker run -it ${CONTAINER_IMAGE_NAME} /bin/bash
```


Authenticate for ecr public access

```Bash
aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws

```

Push image to public ecr repository

```Bash

docker tag nba-mlflow-dag:latest public.ecr.aws/w6w5s2w4/nba-ml

docker push public.ecr.aws/w6w5s2w4/nba-ml
```
