# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = ReimaginedQuantum
SOURCEDIR     = source
BUILDDIR      = build

run : mainwindow.py channels.py mainGUI.py reimaginedQuantum.py GUI_images.py
	python mainGUI.py && rm -r __pycache__ && clear

git : mainGUI.py
	git add . && git commit -m "from make" && git push origin master

Quantum : mainwindow.py channels.py main.py core.py GUI_images.py main.spec
	pyinstaller --windowed --icon=GUI/icon.ico --hidden-import=PySide main.py
#	mv dist/main Quantum
#	rm -r dist build __pycache__

GUI_images.py : GUI/icon.png GUI/splash.png GUI/GUI_images.qrc
	pyrcc5 GUI/GUI_images.qrc > GUI_images.py

channels.py : GUI/channels.ui
	pyuic5 GUI/channels.ui > channels.py

mainwindow.py : GUI/mainwindow.ui
	pyuic5 GUI/mainwindow.ui > mainwindow.py

html : 
	$(SPHINXBUILD) -b html $(SOURCEDIR) $(BUILDDIR)/html
pdf :
	$(SPHINXBUILD) -b latexpdf $(SOURCEDIR) $(BUILDDIR)/latex
