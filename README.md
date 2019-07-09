# ansible-image


```
DATE="$(date +%Y-%m-%dT%H-%M-%S%z)"
docker build . -t docker.io/port/ansible-image:${DATE}; docker push docker.io/port/ansible-image:${DATE}
```
