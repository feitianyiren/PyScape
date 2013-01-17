#!/bin/bash

mkdir -p mono

for i in *.wav
do
echo $i
sox $i -c 1 mono/$i
done

