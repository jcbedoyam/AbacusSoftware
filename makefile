# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = ReimaginedQuantum
SOURCEDIR     = source
BUILDDIR      = build

# python -m PyQt5.uic.pyuic youruifile -o yourpyfile -x

TARGETS = Software/__mainwindow__.py Software/__channels__.py Software/mainGUI.py\
 		Software/__GUI_images__.py Software/__default__.py\
		Software/__about__.py Software/__uninstaller__.py

run : install run_software

install :
	cd Python && python setup.py install && rm -r build

installer : Software/installer.py Software/__installer__.py $(TARGETS)
	cd Software && python compile.py

Software/__installer__.py : Software/GUI/Installer/dialog.ui
	pyuic5 $< > $@

Software/__uninstaller__.py : Software/GUI/Uninstaller/dialog.ui
	pyuic5 $< > $@

run_software : $(TARGETS)
	cd Software && python mainGUI.py && rm -r __pycache__ && clear

Software/__GUI_images__.py : Software/GUI/Program/GUI_images.qrc Software/GUI/Program/icon.png Software/GUI/Program/splash.png Software/GUI/Program/uninstall.ico
	pyrcc5 $< > $@

Software/__channels__.py : Software/GUI/Program/channels.ui
	pyuic5 $< > $@

Software/__mainwindow__.py : Software/GUI/Program/mainwindow.ui
	pyuic5 $< > $@

Software/__default__.py : Software/GUI/Program/default.ui
	pyuic5 $< > $@

Software/__about__.py : Software/GUI/Program/about.ui
	pyuic5 $< > $@

html :
	$(SPHINXBUILD) -b html $(SOURCEDIR) $(BUILDDIR)/html
	rm -r docs/* && mv build/html/* docs/ && rm -r build

pdf :
	$(SPHINXBUILD) -b latexpdf $(SOURCEDIR) $(BUILDDIR)/latex
