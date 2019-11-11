#! /bin/bash
id=$(ps axf|grep mplayer|grep -v grep|awk '{print $1}')
kill -STOP $id
echo $id