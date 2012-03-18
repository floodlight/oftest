#
# Simple make file to generate OpenFlow python files
#
# Fixme:  Would like pylibopenflow to be able to run remotely
# Currently, we have to cd to it's dir and refer back to local

TOP_DIR = ../..
TOOLS_DIR = ..
DOC_DIR = ${TOP_DIR}/doc
TESTS_DIR = ${TOP_DIR}/tests

PYLIBOF_DIR = ${TOOLS_DIR}/pylibopenflow

TARGET_DIR = ${TOP_DIR}/src/python/oftest
SETUP_DIR = ${TOP_DIR}/src/python/

# Relative to pyopenflow-pythonize exec location
OF_HEADER = include/openflow.h

# Relative to here
ABS_OF_HEADER = ${PYLIBOF_DIR}/${OF_HEADER}

PYTHONIZE = bin/pyopenflow-pythonize.py
CSTRUCT_GEN_CMD = (cd ${PYLIBOF_DIR} && ${PYTHONIZE} -i ${OF_HEADER} \
	${TARGET_DIR}/cstruct.py)
CSTRUCT_AUX_INFO = ${TARGET_DIR}/class_maps.py

# Dependencies for cstruct.py
CSTRUCT_DEP = ${ABS_OF_HEADER} $(wildcard ${PYLIBOF_DIR}/pylib/*.py)
CSTRUCT_DEP += $(wildcard ${PYLIBOF_DIR}/pylib/of/*.py) 

# Generated and other files
GEN_FILES := $(addprefix ${TARGET_DIR}/,cstruct.py message.py error.py \
	action.py)
# class_maps is generated as a side effect of cstruct....
OTHER_FILES :=  $(addprefix ${TARGET_DIR}/,action_list.py parse.py \
	controller.py dataplane.py class_maps.py)
LINT_SOURCE := ${GEN_FILES} ${OTHER_FILES}
LINT_FILES := $(subst .py,.log,${LINT_SOURCE})
LINT_FILES := $(subst ${TARGET_DIR}/,lint/,${LINT_FILES})

all: ${GEN_FILES}

install: all
	(cd ${SETUP_DIR} && sudo python setup.py install)

# The core OpenFlow libraries generated from openflow.h
${TARGET_DIR}/cstruct.py: ${CSTRUCT_DEP}
	${CSTRUCT_GEN_CMD} > ${CSTRUCT_AUX_INFO}

# General rule like src/message.py comes from scripts/message_gen.py
${TARGET_DIR}/%.py: scripts/%_gen.py ${TARGET_DIR}/cstruct.py
	python $< > $@

# The pylint files
lint/%.log: ${TARGET_DIR}/%.py
	mkdir -p lint
	(cd ${TARGET_DIR} && pylint -e $(notdir $<)) > $@

# Note that lint has issues with scapy syntax
lint: ${LINT_FILES}

${TESTS_DIR}/oft.py:
	ln -s oft $@

# For now. just local source doc generated
doc: ${GEN_FILES} ${OTHER_FILES} ${DOC_DIR}/Doxyfile ${TESTS_DIR}/oft.py
	(cd ${DOC_DIR} && doxygen)

clean:
	rm -rf ${GEN_FILES} ${LINT_FILES} ${DOC_DIR}/html/*

test: all
	(cd tests && python msg_test.py) > tests/msg_test.log

help:
	@echo
	@echo "Makefile for oftest source munger"
	@echo "    Default builds python files and installs in ${TARGET_DIR}"
	@echo "    make local:  Generate files and put in src/"
	@echo
	@echo "Targets:"
	@echo "   all:     Puts generated .py in ${TARGET_DIR}"
	@echo "   lint:    Puts error report in lint/*.log"
	@echo "   doc:     Runs doxygen on generated files in ../../doc"
	@echo "   install: Run setup tools for generated python	source"
	@echo "   clean:   Removes generated files"
	@echo
	@echo "Debug info:"
	@echo
	@echo "Files generated GEN_FILES:  ${GEN_FILES}"
	@echo
	@echo "Dependencies for cstruct.py CSTRUCT_DEP:  ${CSTRUCT_DEP}"
	@echo
	@echo "Already created files OTHER_FILES:  ${OTHER_FILES}"
	@echo
	@echo "LINT_FILES:  ${LINT_FILES}"


.PHONY: all local install help doc lint clean test
