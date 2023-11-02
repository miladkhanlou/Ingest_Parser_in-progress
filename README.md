# XML Parser
A tool for parsing Louisiana Digital Library XML files as one of our ETL pipelines.
</br>
On commandline we can tell the code accomplish each of the following tasks separately:</br>

#### 1. Get all the unique Tags and attributes, and write them into a CSV
&emsp;&emsp;i. (-o “name of your tag/attirbute csv) </br>
&emsp;&emsp;ii. (-i “input directory of XML Mods files to find tags and attributes”)</br>
#### 2. Get XML Paths with Frequency , and write them into a CSV , With the option of finding misspelled / non-existent tags and attributes (-e)
&ensp;This requires input tag/attribute csv (-e “input tag/attribute csv filename and path”)</br>
&emsp;&emsp;i. (-o “name of your xml path freq csv) -> used to generate the master xml string file (dictionary)</br>
&emsp;&emsp;ii. (-i “input directory of XML Mods files to find XML strings”) </br>

#### 3. Build workbench csv, with the option of finding misspelled / non-existent tags and attributes (In Progress)
&ensp;This requires input tag/attribute csv (-e “input tag/attribute csv filename and path”)</br>
&emsp;&emsp;i. (-o “name of your workbench csv) </br>
&emsp;&emsp;ii. (-m “(master xml string dictionary)” </br>
&emsp;&emsp;iii. (-I “path to the XML MODS that we are ingesting”)</br>

###### XML2Workbench – taking MODS XML files and converting them to a workbench csv. 

