VENV_NAME?=.venv
PYTHON?=python3
REMOTE?=false

.PHONY: venv install install-remote clean

venv: .venv/bin/python3 
.venv/bin/python3:
	$(PYTHON) -m venv $(VENV_NAME)
	$(VENV_NAME)/bin/pip install --upgrade pip
	$(VENV_NAME)/bin/pip install -r requirements.txt

install: venv
	$(VENV_NAME)/bin/python main.py --local true

install-remote: venv
	$(VENV_NAME)/bin/python main.py --local false --check-knox 

clean:
	rm -rf $(VENV_NAME)
