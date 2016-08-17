Australian Countrywide Data
====

The Geocoded National Address File (referred to as G-NAF) is Australia’s
authoritative, geocoded address file.

G-NAF is one of the most ubiquitous and powerful spatial datasets. It contains
more than 13 million Australian physical address records. The records include
geocodes. These are latitude and longitude map coordinates. G-NAF does not
contain personal information.

G-NAF is produced by PSMA Australia Limited (PSMA), an unlisted public company
formed by the nine governments of Australia to collate and standardise, format
and aggregate location data from each of the jurisdictions into authoritative
location based national datasets.

More information at http://www.data.gov.au/dataset/geocoded-national-address-file-g-naf

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
    
    # build docker image from cache
    curl http://data.openaddresses.io/cache/au/au-docker-e3b835b57.tar.bz2 | bzcat | docker load
    
    # image can alternatively be built the slow way
    docker build -t au-gnaf .
    
    # run cache, leaving data in work directory
    docker run --volume /tmp/work:/work au-gnaf /usr/local/bin/run-cache
    
    # upload contents of cache directory to S3
    aws s3 sync --acl public-read /tmp/gnaf-may16/cache s3://data.openaddresses.io/cache
