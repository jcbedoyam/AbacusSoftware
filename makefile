project : mainwindow.py project.py core.py
	pyinstaller --onefile project.py
	mv dist/project project
	rm -r dist build __pycache__

mainwindow.py : GUI/mainwindow.ui
	pyuic5 GUI/mainwindow.ui > mainwindow.py
