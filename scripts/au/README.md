Australian Countrywide Data
====

Geoscape G-NAF is Australia’s authoritative, geocoded address file. It is
built and maintained by Geoscape Australia using authoritative government data.
Further information about contributors to G-NAF is available
[here](https://geoscape.com.au/legal/data-copyright-and-disclaimer/).

G-NAF is one of the most ubiquitous and powerful spatial datasets. It contains
more than 13 million Australian physical address records. The records include
geocodes. These are latitude and longitude map coordinates. G-NAF does not
contain personal information.

More information at https://data.gov.au/dataset/geocoded-national-address-file-g-naf

Using Docker
----

`gnaf.sh` contains a script for caching G-NAF data with
[gnaf-loader](https://github.com/minus34/gnaf-loader).

`Dockerfile` contains a Docker process for caching G-NAF. Docker allows for
code execution in a controlled environment. On Ubuntu, Docker can be installed
with `apt-get install docker.io`.

    # prepare a temporary work directory for Docker
    mkdir /tmp/work
    chgrp docker /tmp/work
    chmod ugo+rwxt /tmp/work

    # build docker image
    docker build -t au-gnaf .

    # run cache, leaving data in work directory
    docker run --volume /tmp/work:/work au-gnaf /usr/local/bin/run-cache

    # upload contents of cache directory to S3
    aws s3 sync --acl public-read /tmp/work/cache s3://data.openaddresses.io/cache
