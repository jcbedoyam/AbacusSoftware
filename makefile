# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = ReimaginedQuantum
SOURCEDIR     = source
BUILDDIR      = build

run : install run_software

install :
	cd Python && python setup.py install && rm -r build

run_software : Software/__mainwindow__.py Software/__channels__.py Software/mainGUI.py Software/__GUI_images__.py
	cd Software && python mainGUI.py && rm -r __pycache__ && clear

Software/__GUI_images__.py : Software/GUI/icon.png Software/GUI/splash.png Software/GUI/GUI_images.qrc
	pyrcc5 Software/GUI/GUI_images.qrc > Software/__GUI_images__.py

Software/__channels__.py : Software/GUI/channels.ui
	pyuic5 Software/GUI/channels.ui > Software/__channels__.py

Software/__mainwindow__.py : Software/GUI/mainwindow.ui
	pyuic5 Software/GUI/mainwindow.ui > Software/__mainwindow__.py

html :
	$(SPHINXBUILD) -b html $(SOURCEDIR) $(BUILDDIR)/html
	rm -r docs/* && mv build/html/* docs/ && rm -r build

pdf :
	$(SPHINXBUILD) -b latexpdf $(SOURCEDIR) $(BUILDDIR)/latex
