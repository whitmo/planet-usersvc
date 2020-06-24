# User Service (usersvc)

Creates and manages users and groups.

## Technology

Cornice/Pyramid HTTP service backed by firestore (demonstrated here using the [firestore emulator](https://hub.docker.com/r/mtlynch/firestore-emulator)).

Developed and tested on python 3.7.

## Local demo

Requires docker and tox (please read runner script). Requires ports 8080 and 6543 to be free.

```
$ ./setup-dev.sh
```

To exercise the service:

``` sh
$ .tox/py37/bin/usersvc.ftest
```

To clean up run `docker ps` and kill the firestore emulator container
