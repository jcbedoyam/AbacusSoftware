#Quantum : mainwindow.py channels.py main.py core.py
#	pyinstaller --onefile main.py
#	mv dist/main Quantum
#	rm -r dist build __pycache__ main.spec

all : mainwindow.py channels.py main.py core.py
	python main.py && rm -r __pycache__

channels.py : GUI/channels.ui
	pyuic5 GUI/channels.ui > channels.py

mainwindow.py : GUI/mainwindow.ui
	pyuic5 GUI/mainwindow.ui > mainwindow.py
