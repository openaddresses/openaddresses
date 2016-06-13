New Zealand Countrywide Data
====

Land Information New Zealand (LINZ) provides downloadable address data from
its data service website at https://data.linz.govt.nz. The file requires a
user account to retrieve, so it must be cached using this script.

More information at https://data.linz.govt.nz/layer/779-nz-street-address-electoral/

Using Docker
----

`lds-nz.sh` contains a script for caching LDS data. You will need to provide
a copy of _Street Address (Electoral)_ data, which can be downloaded from
Land Information New Zealand’s website. See _Getting Data_ below.

`Dockerfile` contains a Docker process for caching data. Docker allows for code
execution in a controlled environment. On Ubuntu, Docker can be installed with
apt-get install docker.io.

    # prepare a temporary work directory for Docker
    mkdir /tmp/work
    chgrp docker /tmp/work
    chmod ugo+rwxt /tmp/work
    cp lds-nz-street-address-electoral-SHP.zip /tmp/work/

    # build docker image
    docker build -t nz-lds .

    # run cache, leaving data in work directory
    docker run --volume /tmp/work:/work nz-lds /usr/local/bin/run-cache

    # upload contents of cache directory to S3
    aws s3 sync /tmp/work/cache s3://data.openaddresses.io/cache

Getting Data
----

1.  Start by [finding the Street Address (Electoral) dataset](https://data.linz.govt.nz/search/?q=street+address+electoral)
    on [LINZ Data Service](https://data.linz.govt.nz/), and select “download” from
    the drop-down menu:
    
    ![Download data](images/1.png)

2.  Accept the terms of service and create a download. You will be asked to create
    an account on the website with your email address:
    
    ![Create download](images/2.png)

3.  Wait for the downloaded to be created; appears to take ~5 minutes:
    
    ![Wait for creation](images/3.png)

4.  Download the 91MB address shapefile, `lds-nz-street-address-electoral-SHP.zip`:
    
    ![Get file](images/4.png)
