if [[ $# -eq 0 ]] ; then
    echo 'usage: ./collect_song_list.sh artists.txt'
    exit 1
fi

java -cp jsoup-1.8.3.jar:. DownloadAll $1
