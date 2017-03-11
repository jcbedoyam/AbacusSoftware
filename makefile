all : mainwindow.py channels.py main.py core.py GUI_images.py
	python main.py && rm -r __pycache__ && clear

git : main.py
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
