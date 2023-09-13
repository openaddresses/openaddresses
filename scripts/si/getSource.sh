#!/bin/bash
set -e
dest="${1}"
credentialsFile="CREDENTIALS-egp.gu.gov.si.txt"
maxAge=720

countTooOld=3

if [ -f "${dest}KS_SLO_SHP_G.zip" ] ; then
	#check age of existing files
	countTooOld=$(find "${dest}KS_SLO_SHP_G.zip" -mmin +${maxAge} | wc -l)
fi

# exit if all are newer than max age
if [ "$countTooOld" -gt "0" ]; then
	echo "Need to download $countTooOld files (they are either missing or older than $maxAge minutes)"
else
	echo "No need to download anything (source files are already there and not older than $maxAge minutes)"
	exit 0
fi

#------ download all:------
# read possibly existing credentials...
if [ -f $credentialsFile ]; then
	source $credentialsFile
fi

echo Credentials for https://egp.gu.gov.si/egp/

if [ -z "$username" ]; then
    echo -n "	Username: ";
    read -r username
    echo "username=\"$username\"" > $credentialsFile
else
    echo "	Username: '$username'";
fi

if [ -z "$password" ]; then
    echo -n "	Password: ";
    read -r password
    read -p "	Save password in plain text to $credentialsFile for future use? (y/N) " -n 1 -r
    echo    # (optional) move to a new line
    if [[ $REPLY =~ ^[Yy]$ ]]
    then
        # save it only if wanted
        echo "password=\"$password\"" >> $credentialsFile
    fi
else
    echo "	Password: *********";
fi

# Log in to the server.  This can be done only once.
wget --quiet \
     --save-cookies cookies.txt \
     --keep-session-cookies \
     --ca-certificate=sigov-ca2.pem \
     "https://egp.gu.gov.si/egp/login.html"
# example login.html content:
# <input type="hidden" name="_csrf" value="089070ed-b40a-4e3c-ab22-422de0daffff" />
csrftoken="$(sed -n 's/.*name="_csrf"\s\+value="\([^"]\+\).*/\1/p' login.html)"
rm login.html
echo Got CSRF token: "${csrftoken}".

loginFormData="username=${username}&password=${password}&_csrf=${csrftoken}"

wget --quiet --load-cookies cookies.txt \
     --save-cookies cookies.txt \
     --keep-session-cookies \
     --referer https://egp.gu.gov.si/egp/ \
     --post-data "${loginFormData}" \
     --delete-after \
     --ca-certificate=sigov-ca2.pem \
     "https://egp.gu.gov.si/egp/login.html"

# Now grab the data we care about.

#KS_SLO_SHP_G.zip
wget --load-cookies cookies.txt \
     --directory-prefix "${dest}" \
     --content-disposition -N \
     --ca-certificate=sigov-ca2.pem \
     "https://egp.gu.gov.si/egp/download-file.html?id=191&format=10&d96=1"

rm cookies.txt

#----- extract: -------

for file in "${dest}"KS_SLO_*.zip; do extdir=$(basename "$file" .zip); echo "$extdir"; rm -rf "${dest}${extdir}"; unzip -o -d "${dest}$extdir" "$file"; done

echo getSource finished.
