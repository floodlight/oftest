# How Can I Contribute?

We're always willing to accept good pull requests (PRs). In case you're stuck for ideas on where to start, here are some ideas to get you started.

## Add Missing Test Cases

We welcome any patch that adds a missing test (or improves an existing one, for that matter). In this regard, while they make for heavy reading, the [OpenFlow Specifications](https://www.opennetworking.org/sdn-resources/onf-specifications/openflow) are likely the best places to start. Once you have an idea of a test you'd like to implement just check the [Adding Your Own Test Cases](#adding-or-modifying-tests) section below.

## Bug Fixes

Humans will inevitably write buggy software. If you spot a bug in either a test cases or another element of the framework then either [submit a fix](https://github.com/floodlight/oftest/pulls) or [file a bug](https://github.com/floodlight/oftest/issues).

## Add New Features

Need to modify OFTest to fit a personal need or business requirement? Great! If you think it'll be useful to anyone else then submit a PR for review.

## Documentation & Other Changes

Using OFTest in a unique way? Finding OFTest difficult to set up and wanting to help others avoid your issues? Finding yourself annoyed by a typo in some code/documentation? Submit a pull request!

---

# Making Changes

## Adding or Modifying Tests

OFTest itself uses the `unittest` library, which is part of the Python Standard Library. This means there are some requirements for tests written for OFTest:

 * Each new test case should be its own class.
 * All tests must inherit from `unittest.TestCase` or an existing test. Most tests will inherit from `oftest.base_tests.SimpleDataPlane`.
 * Tests must also provide a `runTest` function, which will act as the main routine for all test cases. This is also how OFTest discovers tests.
 * Tests should use the `unittest` assert cases, defined [here](https://docs.python.org/2/library/unittest.html#assert-methods), as they provide more information to the user about issues that standard the standard `assert`.
 * Tests may provide a `setUp` and/or `tearDown` function. These will be automatically called by the test framework before/after calling `runTest` respectively. If overriding an existing test be sure to call the super class' `setUp` or `tearDown` functions.

We suggest you look at `basic.py` as a starting point for writing new tests. It's also worth noting these conventions:

 * The first line of the doc string for a file and for a test class is displayed in the list command. Please keep it clear and under 50 characters.

### Coding Style

OFTest uses the Python Standard Style Guide, or [PEP-8](http://www.python.org/dev/peps/pep-0008/). Please ensure all changes abide by this standard.

In addition, when adding new tests, the test file names should be lowercase with underscores and short, meaningful names. Test case class names should be CamelCased and use similarly short, meaningful names.

## Documentation

Any additional documentation added to the repository should be in [GitHub-flavored Markdown](https://help.github.com/articles/github-flavored-markdown/).

---

# Architecture

The directory structure is currently:

    <oftest>
        `
        |-- oft
        |-- docs
        |-- src
        |   `-- python
        |       `-- oftest
        |-- tests
        |   `-- test cases for OpenFlow 1.0
        |-- tests-1.x
        |   `-- test cases for a specific version
        `-- tools

## Base Test Types

Once installed  the components of OFTest are available via import of submodules of `oftest`. Typically, new tests will be written as subclasses of one of the two following tests:

 * The basic protocol test, `SimpleProtocol`, is used for tests that require only communication with the switch over the controller interface
 * The basic dataplane test, `SimpleDataPlane` is used for tests that require both communication with the switch and the ability to send/receive packets to/from OpenFlow ports.

SimpleProtocol and SimpleDataPlane are defined in `oftest/base_tests.py`.

### Simple Protocol

The essential object provided by inheritance from `SimpleProtocol` (and from `SimpleDataPlane` which is a subclass of `SimpleProtocol`) is `self.controller`. The `setUp` routine ensures a connection has been made to the SUT prior to returning. Thus, in `runTest` you can send messages across the control interface simply by invoking methods of this control object. These may be sent unacknowledged or done as transactions (which are based on the XID in the OpenFlow header):

    import oftest.base_tests as base_tests

    class MyTest(basic.SimpleProtocol):
    ... # Inside your runTest:
        self.controller.message_send(msg)   # Unacknowledged
        self.controller.transact(request)   # Transaction based on XID

### SimpleDataPlane

`SimpleDataPlane` inherits from `SimpleProtocol`, so you get the controller object as well as the dataplane object, `self.dataplane`.

Sending packets into the switch is done with the `send` member:

    import basic

    class MyDPTest(basic.SimpleDataPlane):
    ... # Inside your runTest:
        pkt = simple_tcp_packet()
        self.dataplane.send(port, str(pkt))

Packets can be received in the following ways:

 * Non-blocking poll:

        (port, pkt, timestamp) = self.dataplane.poll()

 * Blocking poll:

        (port, pkt, timestamp) = self.dataplane.poll(timeout=1)

    For the calls to poll, you may specify a port number in which case only packets received on that port will be returned.

        (port, pkt, timestamp) = self.dataplane.poll(port_number=2, timeout=1)

 * Register a handler:

        self.dataplane.register(handler)

### DataPlaneOnly

Occasionally, it is convenient to be able to send a packet into a switch without connecting to the controller. The DataPlaneOnly class is the parent that allows you to do this. It instantiates a dataplane, but not a controller object. The classes `PacketOnly` and `PacketOnlyTagged` inherit from `DataPlaneOnly` and send packets into the switch.

## Messages

The OpenFlow protocol is represented by a collection of objects inside the `oftest.message` module. In general, each message has its own class. All messages have a header member and data members specific to the message. Certain variable length data is treated specially and is described (TBD).

Here are some examples:

    import oftest.message as message
    ...
    request = message.echo_request()

`request` is now an `echo_request` object and can be sent via `self.controller`.transact for example.

    msg = message.packet_out()

`msg` is now a packet_out object. `msg.data` holds the variable length packet data.

    msg.data = str(some_packet_data)

This brings us to one of the important variable length data members, the action list. Each action type has its own class. The action list is also a class with an `add` method which takes an action object.

    import oftest.action as action
    ...
    act = action.action_output()   # Create a new output action object
    act.port = egress_port         # Set the action's parameter(s)
    msg.actions.add(act)           # The packet out message has an action list member

Another key data class is the match object. TBD: Fill this out.

TBD: Add information about stats objects.

## Packets

OFTest uses [Scapy](http://www.secdev.org/projects/scapy/) for managing packet data, although you may not need to use it directly. In the example below, we use the function `simple_tcp_packet` from `testutils.py` to generate a packet. The the parse function `packet_to_flow_match` is called to generate a flow match based on the packet.

    from testutils import *
    import oftest.parse as parse
    import ofp
    ...
    pkt = simple_tcp_packet()
    match = parse.packet_to_flow_match(pkt)
    match.wildcards &= ~ofp.OFPFW_IN_PORT

This introduces the low level module `ofp`. This provides the base definitions from which OpenFlow messages are inherited and basic OpenFlow defines such as `OFPFW_IN_PORT`. Most enums defined in `openflow.h` are available in this module.

---

# Tips & Tricks

## Making Your Tests Configurable

As described in the [README](README.md#passing-parameters-to-tests), you can test for these parameters by importing `testutils.py` and using the function:

    my_key1 = testutils.test_param_get(self.config, 'key1')

The `config` parameter is the global configuration structure copied into the base tests cases (and usually available in each test file). The routine returns `None` if the key was not assigned in the command line; otherwise it returns the value assigned (`17` in this example).

Note that any test may look at these parameters, so use some care in choosing your parameter keys.

## Adding Support for a New Platform

As described in the [README](README.md#platforms), OFTest provides a method for specifying how packets should be sent/received to/from the switch. The "config files" that enable this are known as "platforms".

You can add your own platform, say `gp104`, by adding a file `gp104.py` to the
`platforms` directory. This file should define the function `platform_config_update`. This can be enabled using the `--platform=gp104` parameter on the command line. You can also use the `--platform-dir` option to change which directory is searched.

IMPORTANT: The file should define a function `platform_config_update` which takes a configuration dictionary as an argument and updates it for the current run. In particular, it should set up `config["port_map"]` with the proper map from OpenFlow port numbers to OpenFlow interface names.

## Troubleshooting

Normally, all debug output goes to the file `oft.log` in the current directory. You can force the output to appear on the terminal (and set the most verbose debug level) with these parameters added to the oft command:

    --verbose --log-file=[path/to/logfile]

---
