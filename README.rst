==============
XCSoar Setting
==============

Settings for my XCSoar running on a raspberry pi im my LAK 17a.


File Structure
==============

settings in the xcsoar data directory
-------------------------------------

xcdata always contains data copies based on the settings defined in setup.py.

::
    .xcsoar/
        booter.json
        profile.prf
        Default.tsk
        data/
            waypoint1.cup
            waypoint2.cup
            airspace1.txt
            airspace2.txt
            map.xcm
            checklist.txt
            events.txt
            plane.xcp
            tasks/
                ...


Manage Settings
===============

There are different sources for settings.


From Git Repository
-------------------

Together with the booter code different settings are provided. This can be
used to update settings without the need of a USB stick if there is an
internet connection to github is available.

The booter provides the possibility to pull from github and to select the
provided settings.


From USB
--------

If a USB stick is inserted it is possible to copy already prepared settings
into XCSoar.

File structure on the stick::

xcdata/
    settings/
        <setting name>/
            ... -> files to copy directly into xcsoar data directory


booter.json
===========

::
    {
        "name": "<name>",
        "created": "<date>",
        "source": "git|usb",
        "usb": {
            "copied": [<filelist>]
        },
    }
