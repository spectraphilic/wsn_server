For development install ClickHouse as explained here,
https://clickhouse.com/docs/en/install#quick-install

For example I have downloaded the clickhouse binary in the ~/opt/clickhouse/
directory, and run it from there:

    ~/opt/clickhouse $ ./clickhouse server

Then run the client in another terminal, and created the database:

    ~/opt/clickhouse $ ./clickhouse client
    [...]
    localhost :) CREATE DATABASE wsn;
