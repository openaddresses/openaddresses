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

Experimental Docker (Incomplete)
----

`gnaf.sh` contains a script for caching G-NAF data with
[gnaf-loader](https://github.com/minus34/gnaf-loader).

`Dockerfile` contains an experimental Docker process for caching G-NAF.  We are
experimenting with Docker because it allows for code execution in a controlled
environment. Docker support is incomplete, but can be partially completed using
these commands:

    # prepare a temporary work directory for Docker
    mkdir /tmp/work
    chgrp docker /tmp/work
    chmod ugo+rwxt /tmp/work
    
    # build docker image
    docker build -t au-gnaf .
    
    # run cache, leaving data in work directory
    docker run -i -t --volume /tmp/work:/work au-gnaf /usr/local/bin/run-cache
