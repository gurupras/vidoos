#!/bin/bash

if [[ $# -ne 2 ]]; then
	echo $0 'DIRECTORY' 'PREFIX'
	exit 1
fi

WORKING_DIRECTORY="$1"
PREFIX="$2"

cd $WORKING_DIRECTORY
FILES=`ls $PREFIX*.ts | tr '\n' '|'`
echo $FILES
avconv -i concat:"$FILES" -c copy -y 'stitched.mp4'
