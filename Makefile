GH-PAGES = ${HOME}/dev/urubu-gh-pages/

all: build

build:
	python3 -m urubu build
	touch _build/.nojekyll

serve:
	python3 -m urubu serve

publish:
	git add -A
	git commit
	git push occasional_prayers master

git:
	git push origin master
