PACKAGE1 := programs
PACKAGE2 := share
DEPENDENCIES := pip setuptools build mypy
DEPENDENCIES += attrs jsonrpclib-pelix pydispatcher pyserial
DEPENDENCIES += setec-isplpc==1.* setec-libtester==1.* setec-tester==1.*
DEPENDENCIES += setec-updi==1.* setec-utility[erp]==1.*
SOURCES := $(wildcard $(PACKAGE1)/*.py) $(wildcard $(PACKAGE1)/*/*.py)
SOURCES += $(wildcard $(PACKAGE2)/*.py) $(wildcard $(PACKAGE2)/*/*.py)
SOURCES += $(wildcard *.toml)
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
