#!/bin/bash

# Simple CI for ShutIt

FORCE=0
SHUTIT_BUILD_DIR="/tmp/shutit_builddir"
mkdir -p $SHUTIT_BUILD_DIR
LOCKFILE="${SHUTIT_BUILD_DIR}/shutitci.lck"
LOGFILE="${SHUTIT_BUILD_DIR}/shutit_build_${RANDOM}.log"
if [[ -a $LOCKFILE ]]
then
	echo "Already running"
	exit 
else
	touch $LOCKFILE
fi

git fetch origin master
# See if there are any incoming changes
updates=$(git log HEAD..origin/master --oneline | wc -l)
git log HEAD..origin/master --oneline 
if [[ $updates -gt 0 ]] || [[ $FORCE -gt 0 ]]
then
	git pull origin master
	./test.sh > $LOGFILE || EXIT_CODE=$?
        if [[ $EXIT_CODE -ne 0 ]]
	then
		tail -100 $LOGFILE | mail -s "ANGRY SHUTIT" ian.miell@gmail.com
	else
		echo OK | mail -s "HAPPY SHUTIT" ian.miell@gmail.com
	fi
	rm -f $LOGFILE
fi

rm -rf $SHUTIT_BUILD_DIR