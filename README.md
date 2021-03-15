Problem:
--------
The repository of h-brs.de is based on OPUS4. It can export our full metadata
only in XML format.

Solution:
---------
Program parses downloaded XML file from OPUS4 repository. User can chose between available 
document types. The selection will be converted to a chosen file type (CSV, JSON or TXT).

Uses standard library except Beautiful Soup:

$ pip install bs4

Option 1:
---------
* Use via console: $ python opusxmlextractor.py
* By default it uses an OPUS4 XML file within the working
  directory and shows available document types.
* Chose document types and file types (CSV, JSON, TXT).
* The new file is stored in the working directory.

Option 2:
---------
* Instantiate object with OPUSXMLExtractor()
* Check document types with identify_available_doc_types()
* Use to_csv(), to_txt() or to_json() to convert. Pass filename and 
  document types as arguments. File name accepts string without file extension.
  Doc_types accepts list or tuple. No args passed: File name is random id.
  Program converts all document types.

