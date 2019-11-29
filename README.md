# Metropolis (Python Microservice Gateway with NATS)

> Can we make `simple`, `scalable`, `observable`, `operable` service gateway?

## Purpose

### Cloud Native

### Single Workload Unit

### Service Discovery

### Service Mesh

## Architecture Concept

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
  |       |                            |                       |
  |       +--------------+-------------+                       |
  |                      |                                     |
  |                   Ingress                                  |
  +--------------------- | ------------------------------------+
                         V
```

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
