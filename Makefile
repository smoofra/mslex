
version=1.1.0

WHEEL=dist/mslex-$(version)-py3-none-any.whl
SDIST=dist/mslex-$(version).tar.gz
all: wheel sdist

.PHONY: all test lint format doc docs wheel sdist publish

test:
	tox

lint:
	tox -e flake8,black

format:
	black -l99 .

docs doc &:
	make -C docs html

wheel: $(WHEEL)
sdist: $(SDIST)

$(WHEEL) $(SDIST) &: setup.* mslex/*.py *.rst MANIFEST.in *.rst docs/* tests/*
	python -m build

publish: $(WHEEL) $(SDIST)
	twine upload $(WHEEL) $(SDIST)

ifeq ($(filter grouped-target,$(value .FEATURES)),)
$(error Unsupported Make version ($(MAKE_VERSION)).  Use GNU Make 4.3  or above)
endif
