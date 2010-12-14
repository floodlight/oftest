all:
	@echo Per the INSTALL instructions:
	@echo cd ../../tools/munger
	@echo sudo make install
	@echo 
	@echo This Makefile is only for developers. Current targets:
	@echo make lint 	-- runs pylint on all the code
	@echo make tests 	-- runs all of the internal unit tests

lint:
	cd oftest && pylint --rcfile=../pylint.conf *.py ; cd ../ofps   && pylint --rcfile=../pylint.conf *.py 


tests:
	@echo --------- OFTEST unittests
	./oftest/unittests.py
	@echo --------- OFPS unittests
	./ofps/unittests.py
