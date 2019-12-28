# Metropolis

- CNCF의 `NATS` Messge를 사용한 메시징 기반의 마이크로서비스 프레임워크
- Written in `Python`

## Purpose

마이크로 서비스 아키텍쳐가 전통적인 모놀리식 서비스 아키텍쳐가 가진 단점을 보완하고 있고,
그에 따라 워크로드를 더 작은 규모로 관리하기 위한 솔루션(container, orchestrator)들이
등장하게 되면서 보편적인 아키텍쳐 패턴으로 점점 자리를 잡아가고 있다.

하지만 아직까지 분리되는 마이크로 서비스들을 효율적으로 관리하기 위해서는 전통적인 모놀리식
서비스를 운영하는 경험 이외에 필요한 개념(Discovery, Governance, Service Mesh)들도 중요해지고 있다.

`CNCF` 생태계 도구들을 이용하여 간단한 메시지 기반의 마이크로 서비스 프레임워크를 제작해
보고, 서비스를 구동해 보면서 `Cloud Native`환경에서 서비스들을 좀 더 효율적으로 관리하고
개발해 나갈 수 있는 방법을 제시해 본다.

### `CNCF` ecosystems

#### Orchestration - Kubernetes

컨테이너화 된 워크로드들을 분산 환경에서 효율적으로 관리하기 위한 오케스트레이터 프로젝트

#### Messaging Bus - Nats

Text 기반의 메시지 버스 프로젝트

#### Metric - Prometheus

#### Logging - Fluentd, Elastic Search

#### Tracing

## Architecture Concept

### Structure

``` txt
  +- Cluster --------------------------------------------------+
  |                                                            |
  |  +- Node-1 --+  +- Node-2 -+  +- Node-3 --+  +- Node-4 -+  |
  |  |           |  |          |  |           |  |          |  |
  |  | Worker-a  |  |          |  |           |  | Worker-d |  |
  |  | Worker-b  |  | Worker-c |  | Worker-a  |  | Worker-c |  |
  |  |    |      |  |    |     |  |    |      |  |    |     |  |
<======= NATS ========= NATS ======================= NATS =======>
  |  |    |      |  |          |  |    |      |  |          |  |
  |  |  Gateway  |  |          |  |  Gateway  |  |          |  |
  |  |    |      |  |          |  |    |      |  |          |  |
  |  +--- | -----+  +----------+  +--- | -----+  +----------+  |
  |       +---------- Ingress ---------+                       |
  +--------------------- | ------------------------------------+
                         V
```

### Single Workload Unit

### Components

#### Nats

Message bus

#### Worker

Business Logic worker

#### Gateway

Service gateway

## Example

### Install metropolis

``` sh
$ pip install metropolis
```

### Define Worker task

``` python
from metropolis import Worker


worker = Worker(nats='nats://localhost:4222')


@worker.task(subject='foo.bar', queue='worker')
def mytask(data, *args, **kwargs):
    """Simple task which returns reverse string
    """

    return data[0][::-1]


worker.run()
```

### Define Gateway

``` python
from metropolis import Gateway
import settings


gateway = Gateway(nats='nats://nats:4222')
gateway.app.run(host='0.0.0.0')
```

## License

[MIT](./LICENSE.md)
