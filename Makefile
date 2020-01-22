all:	git

git:
	git add .
	git commit -am "`date -u +%Y%m%d-%H:%M:%S`" --no-edit
	git push -u origin master
	exit

git-resync:
	git fetch origin
	git reset --hard origin/master
	git clean -f -d
	exit

