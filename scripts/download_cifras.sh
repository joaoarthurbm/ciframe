mkdir cifras_erro
while read line; do
    dir=`echo $line | awk -F'/' '{print $4}'`
    song=`echo $line | awk -F'/' '{print $5}'`
    if [ ! -d "cifras_erro/$dir" ]; then
      mkdir cifras_erro/$dir
    fi
    curl $line > cifras_erro/$dir/$dir_$song.html
done < $1
