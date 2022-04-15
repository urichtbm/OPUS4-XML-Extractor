# -*- coding: utf-8 -*-
"""

Parses XML file from OPUS4 university repository. User can use the program via
console. The program reads by default an OPUS4 XML file within the working
directory and shows available document types. User can chose document types
and file types (CSV, JSON, TXT). The new file is stored in the working directory.

"""


from bs4 import BeautifulSoup
import csv
from datetime import datetime
import glob
import json
import os
from pprint import pprint
import uuid
 

class OPUSExtractor:
    def __init__(self, file=None):
        if file is None:
            self.file = glob.glob("*.xml")
            self.file = self.file[0]
        else:
            self.file = file
            
        self.opus_soup = self.cook_soup_with_xml_file()
    
    
    # -----------------------------
    # Methods for fetching elements
    # -----------------------------
    
    def get_persons(self, doc, role):
        """
        
        Args
        ----
        str
            role: Completes different "Person" elements in XML soup.
                    
        Returns
        -------
        dict
            Persons associated with the document (e.g. authors, referees).
            
        """
        persons = doc.find_all(f"Person{role.title()}")
        persons = [f"{p.get('FirstName', '')} {p.get('LastName', '')}"
                   for p in persons]
        if not persons:
            persons = ""
            
        return "|".join(persons)


    def get_publication_year(self, doc):
        year = doc.get("PublishedYear")
        if not year:
            try:
                year = doc.find("PublishedDate")
                year = year.get("Year", "")
            except:
                year = ""
            
        return year
    
    
    def get_title_parent(self, doc):
        """
        
        Returns
        -------
        dict
            XML elements which do not require special treatment.
            
        """
        element = doc.find("TitleParent")
        if element:
            return element.get("Value", "")
        else:
            return ""
        
        
    def get_identifier(self, doc, type_):
        identifiers = doc.find_all("Identifier")
        for i in identifiers:
            if i["Type"] == type_ :
                return i.get("Value", "")
        return ""    
        
        
        
    # -----------------------------------------------------------------
    # Methods to fetch elements for 'Kerndatensatz-Forschung' (kds)
    # -----------------------------------------------------------------
    
    def get_enrichment_fields(self, doc):
        enrichments = doc.find_all("Enrichment")
        
        return {f"enrichment_{(e.get('KeyName', '')).lower()}":
                e.get("Value", "") for e in enrichments} 
    
            
    def get_collection_fields(self, doc):
        required_collection_types = ("kds_type_publicationtype",
                                     "kds_type_documenttype")
        dic = {}
        for c in doc.find_all("Collection"):
            if c.get("RoleName") in required_collection_types:
                dic[c.get("RoleName")] = c.get("Name", "")
                
        return dic
                


    # ------------------------------------------------------------
    # Methods for additional elements from specific document types
    # ------------------------------------------------------------      

    def get_journal_data(self, doc):
        return {"parent_title": self.get_title_parent(doc),
                "issue": doc.get("Issue", ""),
                "volume": doc.get("Volume", ""),
                "page_first": doc.get("PageFirst", ""),
                "page_last": doc.get("PageLast", ""),
                "doi": self.get_identifier(doc, "doi"),
                "issn": self.get_identifier(doc, "issn"),}
# IdentifierDoi      

    def get_conference_object_data(self, doc):
        return {"parent_title": self.get_title_parent(doc),
                "doi": self.get_identifier(doc, "doi"),}
        
    
    def get_book_collection_data(self, doc):
        return {"collection_title": self.get_title_parent(doc),
                "page_first": doc.get("PageFirst", ""),
                "page_last": doc.get("PageLast", ""),
                "doi": self.get_identifier(doc, "doi"),}  
         
    
    def get_book_data(self, doc):
        return {"publisher": doc.get("PublisherName", ""),
                "place": doc.get("PublisherPlace", ""),
                "isbn": self.get_identifier(doc, "isbn"),}      
    
    
    def get_thesis_data(self, doc):
        date_accepted = doc.find("ThesisDateAccepted")
        if date_accepted:
            date_accepted = datetime \
                .fromtimestamp(int(date_accepted["UnixTimestamp"])) \
                    .strftime("%Y-%m-%d")
                    
        return {"accepted": date_accepted, 
                "doi": self.get_identifier(doc, "doi"),
                "referees": self.get_persons(doc, "referee"),
                "advisors": self.get_persons(doc, "advisor"),}
            
    
    # creating cooperation always empty!
    def get_grey_lit_data(self, doc):
        return {"contributingcorporation": doc.get("ContributingCorporation", ""),
                "creatingcorporation": doc.get("CreatingCorporation", ""),
                "isbn": self.get_identifier(doc, "isbn"), 
                "doi": self.get_identifier(doc, "doi"),}
        
    
    
    # -------------------------------------------
    # 'Control center' for specific document data 
    # -------------------------------------------
    
    def get_specific_doc_data(self, doc, doc_type):
        return {"article": self.get_journal_data(doc),
                'contributiontoperiodical': self.get_journal_data(doc),
                'periodicalpart': self.get_journal_data(doc),
                'bachelorthesis': self.get_thesis_data(doc), 
                'doctoralthesis': self.get_thesis_data(doc), 
                'masterthesis': self.get_thesis_data(doc),
                'conferenceobject': self.get_conference_object_data(doc),
                'bookpart': self.get_book_collection_data(doc) ,
                "book": self.get_book_data(doc),
                }.get(doc_type, self.get_grey_lit_data(doc))
    
    
    
    # ------------------------
    # Methods for saving files
    # ------------------------
    #
    # Args
    # ----   
    #    str
    #        filename: No file extension. Default None creates random id.
    #    
    #    list or tuple
    #        doc_types: Document types to convert. Default None converts all.
    # -----------------------------------------------------------------------
    
    def to_csv(self, filename=None, doc_types=None):           
        filename, doc_types = self.check_arguments(filename, doc_types)
        docs = self.get_preferred_document_types(doc_types)
        header = {k for d in docs for k in d.keys()}
        
        with open(f"{filename}.csv", "a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=header)
            if file.tell() == 0:
                writer.writeheader()
            for dic in docs:
                # Supplements dic with all header names to fit into CSV.
                new_dic = {h: dic.get(h, "") for h in header }
                writer.writerow(new_dic) 
            
        print(f"\nCSV saved to {os.getcwd()}.")
            
    
    def to_json(self, filename=None, doc_types=None):
        filename, doc_types = self.check_arguments(filename, doc_types)
        docs = self.get_preferred_document_types(doc_types)
        
        with open(f"{filename}.json", "w") as f:
            f.write(json.dumps(docs))  
            
        print(f"\nJSON saved to {os.getcwd()}.")

        
    def to_txt(self, filename=None, doc_types=None):
        filename, doc_types = self.check_arguments(filename, doc_types)
        docs = self.get_preferred_document_types(doc_types)
  
        with open(f"{filename}.txt", "a", encoding="utf-8") as f:
                [pprint(dic, stream=f) for dic in docs]
        
        print(f"\nTXT saved to {os.getcwd()}.")
        
        
    def check_arguments(self, filename, doc_types):
        if filename is None:
            filename = str(uuid.uuid4()) # A random id.
    
        if not isinstance(doc_types, (list, tuple, type(None))):
            raise TypeError("No valid input. Pass list or tuple.")
            
        return filename, doc_types
        
        
        
    # ----------------------------------
    # Methods for extracting XML content 
    # ---------------------------------- 
        
    def identify_available_doc_types(self):
        """

        Returns
        -------
        list
            All available documents types in alphabetical order.

        """
        types = {i.get("Type", "greylit") for i in self.opus_soup}
        
        return sorted(types)
    
    
    def cook_soup_with_xml_file(self):
        """
        
        Returns
        -------
        BS4 object
            All OPUS4 documents parsed by Beautiful Soup.

        """
        with open(self.file, "r", encoding="utf-8") as file:
            content = file.readlines()
            content = "".join(content)
            soup = BeautifulSoup(content, "lxml-xml")
            
        return soup.find_all("Opus_Document")
           
    
    def get_doc_from_opus_soup(self, doc, doc_type):
        """

        Returns
        -------
        dict
            Meta data of a single document from XML soup.

        """
        title_main = doc.find("TitleMain").get("Value", "") 
        authors = self.get_persons(doc, "author")
        publication_year = self.get_publication_year(doc)
        # Basic meta data all publications share.
        basic_doc_data = {"type": doc_type,
                          "year": publication_year,
                          "author(s)": authors,
                          "title": title_main,}
        # Specific, document-related meta data.
        specific_doc_data = self.get_specific_doc_data(doc, doc_type)
        # Meta data relevant for "Kerndatensatz-Forschung".
        enrichment_fields = self.get_enrichment_fields(doc)
        collection_fields = self.get_collection_fields(doc)
         
        return {**basic_doc_data, **specific_doc_data,
                **enrichment_fields, **collection_fields}    
        
    
    def get_preferred_document_types(self, doc_types):
        """

        Returns
        -------
        list
            Meta data of preferred document types from XML soup.

        """
        return [self.get_doc_from_opus_soup(doc, doc.get("Type")) 
                for doc in self.opus_soup
                if doc_types is None or 
                doc.get("Type") in doc_types]
        
                                         
    def __str__(self):
        """
        
        Returns
        -------
        str
            Information about OPUS4 XML Extractor object.

        """
        date = os.path.getmtime(self.file)
        date =  datetime.fromtimestamp(date).date()
        
        return ("Object:\t\t\t\tOPUS4 XML Extractor\n"
                f"OPUS XML file:\t\t\t{self.file} \n"
                f"Last file modification:\t\t{date} \n"
                f"Number of publications:\t\t{len(self.opus_soup)} \n")
                  
                
def main():
    """
    
    For console.
    
    """
    print("Please wait.")       
    extractor = OPUSExtractor()
    
    print(f"\n{extractor}")
    print("Available document types:\n")
    print(*extractor.identify_available_doc_types(), sep=", ")
    
    answer_doc_types = input(("Set document types, seperate with comma. "
                    "Press Enter for all. > "))
    if answer_doc_types:
        answer_doc_types = answer_doc_types.split(", ")
    else:
        answer_doc_types = None
        
    answer_file_type = input("Chose csv, json or txt > ")
    
    selection = {"csv": extractor.to_csv,
                 "json": extractor.to_json,
                 "txt": extractor.to_txt,}
    
    try:
        print("\nPlease wait.")
        selection[answer_file_type](filename=None, doc_types=answer_doc_types)
    except:
        raise TypeError("No valid file type.")

                
if __name__ == "__main__":
      main()

# os.chdir(r'C:\Users\Wintermute\Documents\XML-Konverter')
# print(os.getcwd())
   
    
