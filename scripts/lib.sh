#!/bin/bash

clean_up() {
	cd $PROJECT_ROOT
	/bin/rm default.profraw  lcov.info *.profraw || true
	cd target
	/bin/rm default.profraw  lcov.info *.profraw || true
	cargo clean
}

check_arg(){
    if [ -z $1 ]
    then
        help
        exit 1
    fi
}

match_arg() {
    if [ $1 == $2 ] || [ $1 == $3 ]
    then
        return 0
    else
        return 1
    fi
}
