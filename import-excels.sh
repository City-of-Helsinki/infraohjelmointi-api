#!/bin/bash

set -e

while getopts 'c:d:p:h' opt; do
  case "$opt" in
    c)
        arg="$OPTARG"
        echo "Processing class hierarchies with '${OPTARG}' file"
        python manage.py hierarchies --file ${OPTARG}
        ;;
    
    d)
        arg="$OPTARG"
        echo "Processing excel files within '${OPTARG}' directory"
        directory=${OPTARG%%/} # remove last / slash character from directory name

        ls  $directory/*xlsx | while read name; do
            file_name=$(basename -- "$name")
            if [[ "$file_name" == "TS"* ]]; then
                python manage.py projectimporter --import-from-plan "$name"
            else
                python manage.py projectimporter --import-from-budget "$name"
            fi
        done; 
        ;;

    p)
        arg="$OPTARG"
        echo "Processing programmers from '${OPTARG}' file"
        python manage.py programmerimporter --file ${OPTARG}
        ;;

    h)
        echo "Usage: $(basename $0) [-c /path/to/classes.xslx] [-d /path/to/excels/files] [-p /path/to/programmers.xlsx]"
        exit 0
        ;;

    :)
        echo -e "option requires an argument.\nUsage: $(basename $0) [-c /path/to/classes.xslx] [-d /path/to/excels/files] [-p /path/to/programmers.xlsx]"
        exit 1
        ;;

    ?)
        echo -e "Invalid command option.\nUsage: $(basename $0) [-c /path/to/classes.xslx] [-d /path/to/excels/files] [-p /path/to/programmers.xlsx]"
        exit 1
        ;;
  esac
done
shift "$(($OPTIND -1))"