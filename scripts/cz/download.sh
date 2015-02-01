mkdir data || true
cd data
rm -rf ../unfetched_urls.txt
for url in $(cat ../seznamlinku.txt); do
    if [ -e `basename $url` ]; then
        echo "skipping $url"
    else
        echo $url >> ../unfetched_urls.txt
    fi
done

cat ../unfetched_urls.txt | parallel -j 2 "echo \"fetching {}\"; curl {} -s -O"
rm ../unfetched_urls.txt && cd ..
