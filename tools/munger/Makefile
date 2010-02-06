#
# Simple make file to generate OpenFlow python files
#
# Fixme:  Would like pylibopenflow to be able to run remotely
# Currently, we have to cd to it's dir and refer back to local

TOP_DIR = ../..
TOOLS_DIR = ..
DOC_DIR = ${TOP_DIR}/doc

PYLIBOF_DIR = ${TOOLS_DIR}/pylibopenflow

TARGET_DIR = ${TOP_DIR}/src/python/oftest/ofmsg

# Relative to pyopenflow-pythonize exec location
OF_HEADER = include/openflow.h

# Relative to here
ABS_OF_HEADER = ${PYLIBOF_DIR}/${OF_HEADER}

PYTHONIZE = bin/pyopenflow-pythonize.py
OFP_GEN_CMD = (cd ${PYLIBOF_DIR} && ${PYTHONIZE} -i ${OF_HEADER} \
	${TARGET_DIR}/ofp.py)

# Dependencies for ofp.py
OFP_DEP = ${ABS_OF_HEADER} $(wildcard ${PYLIBOF_DIR}/pylib/*.py)
OFP_DEP = $(wildcard ${PYLIBOF_DIR}/pylib/of/*.py) 

# FIXME:  There are three types of .py files:
#    ofp.py from pylibopenflow output
#    %.py generated from %_gen.py
#    of_message.py and action_list.py -- hand built, already in src dir

GEN_FILES := $(addprefix ${TARGET_DIR}/,ofp.py message.py error.py action.py)
OTHER_FILES :=  $(addprefix ${TARGET_DIR}/,action_list.py of_message.py)
LINT_SOURCE := ${GEN_FILES} ${OTHER_FILES}
LINT_FILES := $(subst .py,.log,${LINT_SOURCE})
LINT_FILES := $(subst ${TARGET_DIR}/,lint/,${LINT_FILES})

all: ${GEN_FILES}
	@echo "Generated files"

${TARGET_DIR}/ofp.py: ${OFP_DEP}
	${OFP_GEN_CMD}

# General rule like src/message.py comes from scripts/message_gen.py
${TARGET_DIR}/%.py: scripts/%_gen.py ${TARGET_DIR}/ofp.py
	python $< > $@

lint/%.log: ${TARGET_DIR}/%.py
	(cd ${TARGET_DIR} && pylint -e $(notdir $<)) > $@

lint: ${LINT_FILES}

# For now. just local source doc generated
doc: ${GEN_FILES} ${OTHER_FILES} ${DOC_DIR}/Doxyfile
	(cd ${DOC_DIR} && doxygen)

clean:
	rm -rf ${GEN_FILES} ${LINT_FILES} ${DOC_DIR}/html/*

help:
	@echo
	@echo "Makefile for oftest source munger"
	@echo "    Default builds python files and installs in ${TARGET_DIR}"
	@echo "    make local:  Generate files and put in src/"
	@echo
	@echo "Targets:"
	@echo "   all:    Puts generated .py in ${TARGET_DIR}"
	@echo "   lint:   Puts error report in lint/*.log"
	@echo "   doc:    Runs doxygen on generated files in ../../doc"
	@echo "   clean:  Removes generated files"
	@echo
	@echo "Debug info:"
	@echo
	@echo "Files generated GEN_FILES:  ${GEN_FILES}"
	@echo
	@echo "Dependencies for ofp.py OFP_DEP:  ${OFP_DEP}"
	@echo
	@echo "Already created files OTHER_FILES:  ${OTHER_FILES}"
	@echo
	@echo "LINT_FILES:  ${LINT_FILES}"


.PHONY: all local install help doc lint clean
