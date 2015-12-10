if [[ $# -eq 0 ]] ; then
    echo 'usage: download_band_names.sh artistas_por_letra.txt (data directory)'
    exit 1
fi

while read line; do
    out=`echo $line | awk -F'www.cifraclub.com.br\/cifras\/' '{print $2}'`
    out=`echo $out | awk -F'.html' '{print $1}'`
    out+="-artistas"
    curl -o $out $line
done < $1
