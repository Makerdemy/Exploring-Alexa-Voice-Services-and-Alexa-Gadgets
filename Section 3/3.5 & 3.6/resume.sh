#! /bin/bash
id=$(ps axf|grep mplayer|grep -v grep|awk '{print $1}')
kill -CONT $id
echo $id