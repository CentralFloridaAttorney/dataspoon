import datetime
import html

from python.dataspoon.dbtool import DBTool

# This example demonstrates the use of DBTool as a static tool
# The following code inserts the current time in the column named 'time' in the row with a link_key 'xyzzy'
start_time = datetime.datetime.now()
dbtool = DBTool()
dbtool.put('xyzzy', 'time', str(start_time))
value = dbtool.get('xyzzy', 'time')
end_time = datetime.datetime.now()
# The following code prints the elapsed time for writing and reading the value
print('start_time: ' + value)
print('end_time: ' + str(end_time))
elapsed_time = end_time-start_time
print('write and retrieve time in microseconds: ' + str(elapsed_time.microseconds))
print('Finished example!')

string_value = "That's great!"
print(string_value + " = " + html.escape(string_value))
