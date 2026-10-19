# Easier notes reader for Amy. Ace PBL! (and any other courses) :)


## Windows:
Setting up from github (in cmd):\
git clone https://github.com/zshuhanzz/amyreads.git \
cd amyreads\
pip install PySide6 PyMuPDF\
python main.py\

### To build
pyinstaller --onefile --windowed --name AmyReads main.py

## Mac:
git clone https://github.com/zshuhanzz/amyreads.git \
cd amyreads\
pip3 install PySide6 PyMuPDF\
python3 main.py\

### To build: 
build.bat

The output location will be in dist\AmyReads.exe or dist/AmyReads.app
