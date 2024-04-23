# aw-from-manictime
Experimental tool to convert CSV dumps of ManicTime tracking data into ActivityWatch events (pretending that they came from aw-watcher-window). The tool takes a CSV path and inserts all the events into the aw-watcher-window bucket corresponding to the current host.

Note that aw-watcher-window stores in the `app` field the executable name of the active apps, whereas ManicTime doesn't collect that info, and instead stores some "app name" of unclear origin. Currently the converter just puts it into the `app` field anyway, which makes those events slightly abnormal.

## Installation
Install from GitHub via pip:
```
pip install git+https://github.com/RundownRhino/aw-from-manictime
```
This will install the required dependencies too, such as `aw_client`.

## Usage
```
aw-from-manictime path/to/exported/file.csv
```