# h2tomysql

migrate database from h2 to mysql using python and bash

## h2tomysql goal

It's not a tool that will do everything, it's more an example (and not the best some refactoring will be needed to have a cleaner code!)
It can help someone that wants to automate the h2 to mysql migration and doesn't know how to start or how to do it.
If it knows python it can help because the code doesn't deal with all cases and some specific errors can occur like overpassing the
mysql column size limited to 65535 if you have many VARCHAR in your create tables, I managed here only some cases with VARCHAR(4000), VARCHAR(10000) and VARCHAR(20000).
It's not for production purpose!

The bash script downloads the h2 driver and exports the h2 database that should exist in the directory which you execute this command.
The python script analyzed the h2 script and create a mysql script in output that can be used to import into mysql.

I tested only with 3 different h2 database that I found some issues depending the h2 script generated.
I imported my 3 h2 databases into mysql 8.0.25.

    Thanks to Jonas Verhoelen article, it helps me to  start : https://jonas.verhoelen.de/databases/dump-sql-h2-database-file/
     in this example I dealt with migrating 3 different h2 database to have some different kinds of scripts to manage
    do not forget to adapt the user and/or password to access to h2 database here "secret" as example

## h2tomysql usage

### h2tomysql.sh

    first step is to call this small bash that will download the driver sql connect to database in the current directory and generate the h2 script

sh ./h2tomysql.sh

### h2tomysql.py

    second step is to call the python program that parses the h2 script and generate a compatible script for mysql.

python3 h2tomysql.py --help

    H2ToMysql is a python3 program that helps to generate a sql script for import into mysql database.
    H2ToMysql uses Python3
    H2ToMysql tested with mysql 8.0.25
    _____________________________________________________________________________________________________
    WARNING : it doesn't deal with all cases, probably you need to adapt the code to your specific needs!
    _____________________________________________________________________________________________________
    For linux and linux-like OS that have the pre-requisites
    Usage: h2tomysql [options] fromfile tofile
    Required : fromfile  is the file that has the h2 script
    Required : tofile    is the result file that will contain compliant mysql script
    Options:
    -V, --version        Display version number of PyToC compiler
    -H, --help           Display this help
    __________________________________________
    Enjoy!

python3 h2tomysql.py --version
H2ToMysql version 1.0.0

example : supposing you generated a h2.sql that contains the export of h2 script. the command creates a mysql.sql that removes some keywords not allowed with mysql and removes also the comments and the create sequence
Do not forget to use first the h2tomysql.sh to generate your h2.sql (change the name into the bash script)
python3 h2tomysql.py h2.sql mysql.sql

## How to improve it

    * using variables in the bash script and calling the python script directly from the bash script to avoid 2 commands to call
    * refactoring bash script to use some variables and avoid to repeat the h2 script name hard-coded
    * refactoring python code to clean it and be more readable and friendly
