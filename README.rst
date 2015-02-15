======
Sivart
======

A poor man's build farm.

What?
=====

A tool to test installation and test steps of your program on various systems.

How?
====

The architectures, install steps and test scripts are described in a
configuration file, which is processed by ``sivart`` to run various vagrant
boxes with the described configuration, then the tests.

Install
=======

Have a look to ``.sivart.yml`` for the detailed steps, but basically you need
a working ``virtualbox`` and::

    pip install sivart

The run::

    python -m sivart --help

Format
======

Sivart's input is a YAML file that lists configurations, like this::

    my_config:
        box: box_url_or_id
        install:
            - step0
            - step1
        script:
            - step0
            - step1

As your number of config grow, you can use facets to store common config
elements::

    .shared:
        install:
            - step0
            - step1
        script:
            - step0
            - step1

    .config0:
        using:
            - .shared
        box: box0

    .config1:
        using:
            - .shared
        box: box1

which makes it easy to perform the same steps on a 32 and 64 bits machine, for
instance.

Finally, there is a ``env`` configuration to test various parameters, e.g.
various compilers::

    .env0:
        env:
            - CC=gcc CXX=g++
            - CC=clang CXX=clang++

    .env1:
        env:
            - CFLAGS=-O1
            - CFLAGS=-O2
            - CFLAGS=-O3

    run:
        using:
            - env0
            - env1
        script:
            - $CC $CFLAGS hello.c

this runs ``$CC $CFLAGS hello.c`` for the Cartesian product of the combination
of ``.env0`` and ``.env1``.

Have a look to ``examples/*`` for more... examples!

Why?
====

Because I needed an automated way to test the Pythran compiler on various
architecture (32/64 bits), various OS *and* various distribution.
