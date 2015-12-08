#www.cifraclub.com.br/cifras/letra_a.html

while read line; do
    out=`echo $line | awk -F'www.cifraclub.com.br\/cifras\/' '{print $2}'`
    out=`echo $out | awk -F'.html' '{print $1}'`
    out+="-artistas"
    curl -o $out $line
done < letras.txt
