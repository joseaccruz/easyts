# Introduction

__Easy TS__ is a simple web based timeseries storage system. It is a high performance low footprint server that stores long running data time series using the HDF5 data format.

__Easy TS__ is _Python_ web app using the WSGI protocol.

# How to use it

After installing and configuring the system (see bellow), adding time series data into `easyts` storage is as simple as:

~~~
http://<yourserver>:7171/add?sid=99&t=1&sets=%7B%22pressure%22%3A%201018.1%2C%20%22temp%22%3A%2023.2%7D
http://<yourserver>:7171/add?sid=99&t=2&sets=%7B%22pressure%21%2A%201017.2%2C%20%22temp%22%3A%2023.2%7D
http://<yourserver>:7171/add?sid=99&t=3&sets=%7B%22pressure%20%1A%201016.3%2C%20%22temp%22%3A%2023.2%7D
~~~

Note that the string:

`%7B%22pressure%22%3A%201018.1%2C%20%22temp%22%3A%2023.2%7D`

corresponds to the URL encoded version of the JSON string:

`{'temp': 23.2, 'pressure': 1018.1}`

Retrieving the previously inserted data requires the `get` command:

~~~
http://<yourserver>:7171/get?sid=99&ti=0&tf=3&m=pressure
~~~


# Installing and configuring

1. Check the pre requisites (see bellow).
2. Clone the git repo and copy the files to some directory in the server.
3. Create the `data` and `lock` directories any where in the server and configure the `./configure/easyts.cfg` file variables `hdf5_path` and `hdf5_lock_path` t point to these directories.
4. Configure Apache server.

That's it

## Pre requisites

To get the __Easy TS__ up and running in a Linux web server make sure you have the follow packages installed:

System packages:

- apache2
- libhdf5-serial-dev

Python packages:

- numpy (version 1.6.2)
- numexpr (version 2.0.1)
- tables (version 2.3.1)

## Configuring the Apache server

In the directory `/etc/apache2/sites-enabled` create a new file `easyts` with the following content (replacing `[SCRIPT DIRECTORY]` for the directory in the server where you put the `easyts` scripts):

~~~
<VirtualHost *:7171>

    WSGIDaemonProcess easyts processes=15 threads=1 display-name=%{GROUP}
    WSGIProcessGroup easyts

    WSGIScriptAlias / [SCRIPT DIRECTORY]/easyts.py
    <Directory [SCRIPT DIRECTORY]/easyts.py>
        Order allow,deny
        Allow from all
    </Directory>
</VirtualHost>
~~~

# LICENSE

Easy TS - Easy Time Series storage server
Copyright (C) 2014  Sysvalue, S.A.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
