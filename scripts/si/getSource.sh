#!/bin/bash
dest="${1}"
credentialsFile="CREDENTIALS-egp.gu.gov.si.txt"

#------ download all:------
# read possibly existing credentials...
source $credentialsFile

if [ -z "$username" ]; then
    echo -n "Enter Username:";
    read -r username
    echo -n 'username="' > $credentialsFile
    echo -n $username >> $credentialsFile
    echo  '"' >> $credentialsFile
else
    echo "Username: '$username'";
fi

if [ -z "$password" ]; then
    echo -n "Enter Password:";
    read -r password
    read -p "Save in plain text to $credentialsFile for future use? (y/N) " -n 1 -r
    echo    # (optional) move to a new line
    if [[ $REPLY =~ ^[Yy]$ ]]
    then
        # save it only if wanted
        echo -n 'password="' >> $credentialsFile
        echo -n $password >> $credentialsFile
        echo  '"' >> $credentialsFile
    fi
else
    echo "Password: ******";
fi

# Log in to the server.  This can be done only once.
wget --quiet \
     --save-cookies cookies.txt \
     --keep-session-cookies \
     http://egp.gu.gov.si/egp/login.html
# example login.html content:;
# <input type="hidden" name="_csrf" value="089070ed-b40a-4e3c-ab22-422de0daffff" />
csrftoken="`sed -n 's/.*name="_csrf"\s\+value="\([^"]\+\).*/\1/p' login.html`"
rm login.html
echo Got CSRF token: "${csrftoken}".
#cat cookies.txt

loginFormData="username=${username}&password=${password}&_csrf=${csrftoken}"
#echo login form data: $loginFormData

#exit 1
wget --quiet --load-cookies cookies.txt \
     --save-cookies cookies.txt \
     --keep-session-cookies \
     --referer http://egp.gu.gov.si/egp/ \
     --post-data "${loginFormData}" \
     --delete-after \
     http://egp.gu.gov.si/egp/login.html

# Now grab the page or pages we care about.

#RPE_PE.ZIP
wget --load-cookies cookies.txt \
     --directory-prefix "${dest}" \
     --content-disposition -N \
     http://egp.gu.gov.si/egp/download-file.html?id=105

#RPE_UL.ZIP
wget --load-cookies cookies.txt \
     --directory-prefix "${dest}" \
     --content-disposition -N \
     http://egp.gu.gov.si/egp/download-file.html?id=106

#RPE_HS.ZIP
wget --load-cookies cookies.txt \
     --directory-prefix "${dest}" \
     --content-disposition -N \
     http://egp.gu.gov.si/egp/download-file.html?id=107

rm cookies.txt
rm login.htm*

#----- extract: -------
for file in ${dest}RPE_*.ZIP; do extdir=`basename "$file" .ZIP`; echo $extdir; unzip -d "${dest}$extdir" "$file"; done
for file in ${dest}RPE_*/*.zip; do unzip -d "${dest}" "$file"; done


echo getSource finished.
