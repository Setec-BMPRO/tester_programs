PACKAGE1 := programs
PACKAGE2 := share
DEPENDENCIES := pip setuptools build mypy
DEPENDENCIES += attrs jsonrpclib-pelix pydispatcher pyserial
DEPENDENCIES += setec-isplpc setec-libtester setec-tester setec-updi setec-utility[erp]
SOURCES := $(wildcard $(PACKAGE1)/*.py) $(wildcard $(PACKAGE2)/*.py) $(wildcard *.toml)
VENV := .venv
VENV_NEW_FLAG := $(VENV)/_venv_is_new
VPYTHON := $(VENV)/bin/python3
CLEAN_TARGETS := dist *.egg-info
.PHONY: clean venv _venv
# Build the output packages
dist: $(VENV) $(SOURCES)
	@rm -f $(VENV_NEW_FLAG)
	$(VPYTHON) -m build
# Remove output packages
clean:
	@rm -rf $(CLEAN_TARGETS)
# Create the venv
$(VENV):
	python3 -m venv $(VENV)
	@touch $(VENV_NEW_FLAG)
	$(MAKE) _venv
# Update the venv
_venv: $(VENV)
	$(VPYTHON) -m pip install -U $(DEPENDENCIES)
# Update the venv, only if it is not newly created
venv: $(VENV)
	@if [ ! -e $(VENV_NEW_FLAG) ]; then $(MAKE) _venv; fi
	@rm -f $(VENV_NEW_FLAG)
