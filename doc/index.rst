.. solsticepy documentation master file, created by
   sphinx-quickstart on Fri Apr 17 13:39:21 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

solsticepy
==========

`solsticepy` provides a set of Python functions that make the task of setting
up and running a Solstice ray-tracing simulation of a CSP system a little easier. At this stage it has been primarily used for simulations of central-tower CSP systems,  even though Solstice itself is capable of simulating a wider range of system types.

.. toctree::
   :maxdepth: 3
   :caption: Contents:

Create YAML input files for Solstice
====================================
.. autofunction:: solsticepy.gen_yaml

Calculate sun position
======================

.. autoclass:: solsticepy.SunPosition
   :members:
   :undoc-members:


Set up and run Solstice simulations
===================================

.. autoclass:: solsticepy.Master
   :members:
   :undoc-members:

Process the results
===================

.. autofunction:: solsticepy.process_raw_results
.. autofunction:: solsticepy.get_breakdown
.. autofunction:: solsticepy.process_raw_results_dish


Generate new heliostat field layouts
====================================

.. autofunction:: solsticepy.radial_stagger

Preliminary calculation of heliostat field performance
======================================================

.. autoclass:: solsticepy.FieldPF
   :members:
   :undoc-members:

Generate 3D views of a heliostat field
======================================

.. autofunction:: solsticepy.gen_vtk

Find Solstice programs in Windows
=================================

.. autofunction:: solsticepy.find_solstice_root
.. autofunction:: solsticepy.find_prog


Indices and tables
==================

* :ref:`genindex`
* :ref:`search`
