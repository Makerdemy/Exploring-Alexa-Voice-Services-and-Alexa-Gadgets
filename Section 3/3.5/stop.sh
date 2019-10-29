#! /bin/bash
id=$(ps axf|grep mpsyt|grep -v grep|awk '{print $1}')
kill -2 $id
echo $id