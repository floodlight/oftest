These tests are for testing a traditional routing box, e.g., running
FaceBook's FBOSS or a netlink listenner like Open Route Cache (ORC).

While OFTest is meant to test openflow switches, a lot of the same
infrastructure gets reused, so we've decided to keep these
tests in OFTest even though they are not strictly speaking *OpenFlow*
tests.

To run, do something like:

sudo ./oft --test-dir=tests-legacy-l3/ --verbose

