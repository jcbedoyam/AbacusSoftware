run : mainwindow.py channels.py mainGUI.py reimaginedQuantum.py GUI_images.py
	python mainGUI.py && rm -r __pycache__ && clear

git : mainGUI.py
	git add . && git commit -m "from make" && git push origin master

Quantum : mainwindow.py channels.py main.py core.py GUI_images.py main.spec
	pyinstaller --windowed --icon=GUI/icon.ico --hidden-import=PySide main.py
#	pyinstaller --onefile --windowed --icon=GUI/icon.ico --hidden-import=PySide main.py
#	mv dist/main Quantum
#	rm -r dist build __pycache__

GUI_images.py : GUI/icon.png GUI/splash.png GUI/GUI_images.qrc
	pyrcc5 GUI/GUI_images.qrc > GUI_images.py

channels.py : GUI/channels.ui
	pyuic5 GUI/channels.ui > channels.py

mainwindow.py : GUI/mainwindow.ui
	pyuic5 GUI/mainwindow.ui > mainwindow.py

##############################################################
# Minimal makefile for Sphinx documentation
##############################################################

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = ReimaginedQuantum
SOURCEDIR     = source
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

###############################################################
