##### Thanks to Jonas Verhoelen article, it helps me to  start : https://jonas.verhoelen.de/databases/dump-sql-h2-database-file/
### in this example I dealt with migrating 3 different h2 database to have some different kinds of scripts to manage
###  do not forget to adapt the user and/or password to access to h2 database here "secret" as example
##### ___________________________________________________________________________________________________________
#if needed to download specific h2 driver
#wget -O h2.jar https://repo.maven.apache.org/maven2/com/h2database/h2/1.4.197/h2-1.4.197.jar
#create query.sql to dump H2 database
echo "SCRIPT TO 'db-h2dbexample1.sql'" > query_h2dbexample1.sql
java -cp h2.jar org.h2.tools.RunScript -url "jdbc:h2:file:./h2dbexample1" -user sa -password secret -script query_h2dbexample1.sql -showResults
#to remove the two first lines (in my test this is an empty query and the user SA creation)
tail -n +3 db-h2dbexample1.sql > tmp.sql && mv tmp.sql db-h2dbexample1.sql
#in some case erros if no database is selected, you can use variables instead of hard-coded values to improve this tool
sed -i '1 iUSE h2dbexample1;\n' db-h2dbexample1.sql
sed -i '1 iCREATE DATABASE h2dbexample1;\n' db-h2dbexample1.sql
#replace PUBLIC database by our target database
sed -i 's/PUBLIC/h2dbexample1/g' db-h2dbexample1.sql

# second database example
echo "SCRIPT TO 'db-h2dbexample2.sql'" > query_h2dbexample2.sql
java -cp h2.jar org.h2.tools.RunScript -url "jdbc:h2:file:./h2dbexample2" -user sa -password secret -script query_h2dbexample2.sql -showResults
tail -n +3 db-h2dbexample2.sql > tmp.sql && mv tmp.sql db-h2dbexample2.sql
sed -i '1 iUSE h2dbexample2;\n' db-h2dbexample2.sql
sed -i '1 iCREATE DATABASE h2dbexample2;\n' db-h2dbexample2.sql
sed -i 's/PUBLIC/h2dbexample2/g' db-h2dbexample2.sql


# third database example that will use a specific h2 function STRINGDECODE that doesn't exist in mysql creating a fake function.
# example with deactivating the foreign key check when script has data to insert and the script doesn't use the right order...
echo "SCRIPT TO 'db-h2dbexample3.sql'" > query_h2dbexample3.sql
java -cp h2.jar org.h2.tools.RunScript -url "jdbc:h2:file:./h2dbexample3" -user sa -password secret -script query_h2dbexample3.sql -showResults
tail -n +3 db-h2dbexample3.sql > tmp.sql && mv tmp.sql db-h2dbexample3.sql
sed -i '1 iDELIMITER //\nCREATE FUNCTION STRINGDECODE(input_value TEXT(10000)) RETURNS TEXT(10000) DETERMINISTIC BEGIN RETURN input_value;END //;\n' db-h2dbexample3.sql
sed -i '1 iSET FOREIGN_KEY_CHECKS=0;\n' db-h2dbexample3.sql
sed -i '1 iUSE h2dbexample3;\n' db-h2dbexample3.sql
sed -i '1 iCREATE DATABASE h2dbexample3;\n' db-h2dbexample3.sql
sed -i 's/PUBLIC/h2dbexample3/g' db-h2dbexample3.sql

