**SprOWL**
==========

SprOWL is an automatic documenter for Semantic Ontologies written in Python based on the [RDFLib](https://github.com/RDFLib/rdflib) & [Jinja2](http://jinja.pocoo.org/)

**Usage**

python sprowl.py [-h] [-d] [-f FILE] [-i IMG]

_optional arguments:_
>-h, --help     Shows this help message and exit

>-d, --debug    Displays debug messages

>-f FILE, --file FILE   The ontology file in OWL, RDF/XML format to document

>-i IMG, --img IMG      The ontology image file to add to the documentation

>-w, --web  Optionally run a webserver on http://localhost:8181 serving the output static files

**Output**
The program will return a set of static web content files following the structure below:

> ./ontologies

>> css

>>> basic.css

>> img

>>> <ontology_title>.[svg, bmp, jpg, ...]

>> res

>> <ontology_title>.[owl, ttl, rdf, ...]

>> <ontology_title>.html

The resultant files can then be copied into a web-server for them to be served.

_Note:_ It is recommended that the root directory of the web-server where the documents are located matches the base url of the ontology (ie. https://cvr-dcs.com/ont/)

Contact: [Cristian Varela](mailto:cristian@cvr-dcs.com?subject=SprOWL) - CVR Data Consulting Services Ltd.