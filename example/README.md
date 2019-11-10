# Example Application

## Application

### ./app/proxy.py

nats http gateway

### ./app/worker.py

nats worker

### ./app/settings.py

proxy와 워커의 태스크 설정등을 관리한다.

### ./kubernetes

구현된 워커와 프록시, k8s nats operator를 이용해 클러스터를 전개하고 서비스 셋을 구성하기 위한
yaml definition들을 관리

## Steps

``` sh
# nats operator를 k8s cluster에 설치한다.
$ ./example/scripts/install_nats_operator.sh

# example application을 배포한다.
$ kubectl apply -f ./example/kubernetes

# URL test
$ curl http://example-natsgateway.mysite.local/foo?data=asdf
```
