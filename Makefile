PACKAGE1 := programs
PACKAGE2 := share
DEPENDENCIES := pip setuptools build black mypy
DEPENDENCIES += attrs jsonrpclib-pelix pydispatcher pyserial
DEPENDENCIES += setec-isplpc==1.* setec-libtester==1.* setec-tester==1.*
DEPENDENCIES += setec-updi==1.* setec-utility[erp]==1.*
PYSOURCES := $(shell find $(PACKAGE1) -name '*.py')
PYSOURCES += $(shell find $(PACKAGE2) -name '*.py')
SOURCES := $(PYSOURCES) $(wildcard *.toml)
VENV := .venv
VENV_NEW_FLAG := $(VENV)/_venv_is_new
VPYTHON := $(VENV)/bin/python3
PYCACHE := __pycache__
CLEAN_TARGETS := dist *.egg-info
DEEP_CLEAN_TARGETS := $(VENV)
.PHONY: clean deepclean venv _venv
# Build the output packages
dist: $(VENV) $(SOURCES)
	@rm -f $(VENV_NEW_FLAG)
	$(VPYTHON) -m build
# Reformat code
black:
	@$(VPYTHON) -m black $(PYSOURCES)
# Remove output packages and cache files
clean:
	@rm -rf $(CLEAN_TARGETS)
	@find -type d -name $(PYCACHE) -execdir rm -rf {} +
# Remove venv as well
deepclean:
	$(MAKE) clean
	@rm -rf $(DEEP_CLEAN_TARGETS)
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
