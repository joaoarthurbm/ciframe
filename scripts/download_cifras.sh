mkdir cifras
while read line; do
    dir=`echo $line | awk -F'/' '{print $4}'`
    song=`echo $line | awk -F'/' '{print $5}'`
    if [ ! -d "cifras/$dir" ]; then
      mkdir cifras/$dir
    fi
    curl $line > cifras/$dir/$dir_$song.html
done < $1
