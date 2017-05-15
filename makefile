# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = ReimaginedQuantum
SOURCEDIR     = source
BUILDDIR      = build

TARGETS = Software/__mainwindow__.py Software/__channels__.py Software/mainGUI.py\
 		Software/__GUI_images__.py Software/__email__.py Software/__default__.py\
		Software/__about__.py

run : install run_software

install :
	cd Python && python setup.py install && rm -r build

run_software : $(TARGETS)
	cd Software && python mainGUI.py && rm -r __pycache__ && clear

Software/__GUI_images__.py : Software/GUI/GUI_images.qrc Software/GUI/icon.png Software/GUI/splash.png
	pyrcc5 $< > $@

Software/__channels__.py : Software/GUI/channels.ui
	pyuic5 $< > $@

Software/__email__.py : Software/GUI/email.ui
	pyuic5 $< > $@

Software/__mainwindow__.py : Software/GUI/mainwindow.ui
	pyuic5 $< > $@

Software/__default__.py : Software/GUI/default.ui
	pyuic5 $< > $@

Software/__about__.py : Software/GUI/about.ui
	pyuic5 $< > $@

html :
	$(SPHINXBUILD) -b html $(SOURCEDIR) $(BUILDDIR)/html
	rm -r docs/* && mv build/html/* docs/ && rm -r build

pdf :
	$(SPHINXBUILD) -b latexpdf $(SOURCEDIR) $(BUILDDIR)/latex
