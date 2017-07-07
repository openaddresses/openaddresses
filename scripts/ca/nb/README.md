GeoNB Address File
====

The GeoNB Address file is one of two (and the only currently open) address
layers for the province of NB.

Using Docker
----

`geonb.sh` contains a script for caching the data

`Dockerfile` contains a Docker process for caching GeoNB. Docker allows for
code execution in a controlled environment. On Ubuntu, Docker can be installed
with `apt-get install docker.io`.

    # prepare a temporary work directory for Docker
    mkdir /tmp/work
    chgrp docker /tmp/work
    chmod ugo+rwxt /tmp/work

    # build docker image
    docker build -t geonb .

    # run cache, leaving data in work directory
    docker run --volume /tmp/work:/work geonb /usr/local/bin/run-cache

    # upload contents of cache directory to S3
    aws s3 sync --acl public-read /tmp/work/output.csv s3://data.openaddresses.io/cache/uploads/ingalls/ca-nb-province.csv
