# Python Microservice Gateway with NATS Messaging

클라우드 환경(특히 `Kubernetes`)에서 `NATS`를 이용해서 쉽게 확장할 수 있는
마이크로서비스 아키텍쳐에 대한 PoC 프로젝트.

## ToC

- [Python Microservice Gateway with NATS Messaging](#python-microservice-gateway-with-nats-messaging)
  - [ToC](#toc)
  - [Overview](#overview)
  - [NATS](#nats)
  - [Architecture Concept](#architecture-concept)
    - [Components](#components)
    - [Workflow](#workflow)
    - [Pros](#pros)
    - [Cons](#cons)

## Overview

- 보편적으로 내부 서비스들의 통신은 `HTTP` 프로토콜 스펙을 전부 이용하지 않는 경우가 많다.
  - `NATS`를 이용할 경우, 통신을 위해 `HTTP` 프로토콜 스펙을 지키기 위해 발생하는 오버헤드를 줄일 수 있음.
  - **`NATS`를 이용하면서 `HTTP` 스펙의 기능이 필요한 경우, 별도로 만들어 붙여야 하는 문제는 있음.**

- 횡단 관심들을 분리하기 위해 API gateway를 사용하는 경우가 있는데,
  이 경우 `APIGW - backend`간 통신 비용을 줄이는데 `NATS`를 사용하면 성능상 이득을 볼 수 있다.
  - API gateway를 사용하게 되면, 뒷단의 서비스들은 HTTP 스펙으로부터 자유로워 질 수 있음.
  - **이 경우 별도의 `NATS` 게이트웨이가 필요하게 된다.**

- `NATS`를 이용하는 워커와, Endpoint에 대한 HTTP 프록시를 제공하는 프레임워크를 만들어 본다.
- `NATS` 를 쓰게 되면, 흔히 말하는 Actor 모델에서 Mailbox가 없어지는 느낌인데,
  이래도 되는지 모르겠다. (굳이 Actor 모델과 비교한다면...)

## NATS

<https://nats.io/>

- Text based simple protocol
- Light weight, Powerful performance
- No persistency
- Synchronized(Request), Asynchronous(Publish)

## Architecture Concept

``` txt
+- Node-1 --+  +- Node-2 -+  +- Node-3 --+  +- Node-4 -+
|           |  |          |  |           |  |          |
| Worker-a  |  |          |  |           |  | Worker-d |
| Worker-b  |  | Worker-c |  | Worker-a  |  | Worker-c |
|    |      |  |    |     |  |    |      |  |    |     |
|   NATS ========= NATS ======================= NATS   |
|    |      |  |          |  |    |      |  |          |
| HttpProxy |  |          |  | HttpProxy |  |          |
|    |      |  |          |  |    |      |  |          |
+--- | -----+  +----------+  +--- | -----+  +----------+
     |                            |
     +--------------+-------------+
                    |
                  Ingress
```

### Components

- `NATS`: 메시징 채널
- `Worker`: Business Logic 수행
- `HttpProxy`: `NATS <-> HTTP`로 리퀘스트를 프록싱, API Gateway의 역할을 담당한다.

### Workflow

### Pros

### Cons
