""""module to convert RDF ontologies into HTML Webpages"""
import os
import argparse
import sys
import json

from shutil import copyfile
from rdflib import Namespace, Graph, URIRef
from rdflib.namespace import RDF, RDFS
from jinja2 import Environment, PackageLoader
from bottle import route, run, static_file

CONTAINER_DIR = 'ontologies/'
RESOURCE_DIR = 'res/'
CSS_DIR = 'css/'
IMAGE_DIR = 'img/'

# Global Variables
DEBUG = False
WEB = False

# TODO: Check if all namespaces are used.
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
GLOS = Namespace("http://varelahq.com/ont/glossary#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")
DC = Namespace("http://purl.org/dc/elements/1.1/")
VS = Namespace("http://www.w3.org/2003/06/sw-vocab-status/ns#")


def parse_uri_ref(uri: str) -> tuple:
    name = (str(uri).rsplit('#', maxsplit=1)[-1]).split('/')[-1]
    namespace = str(uri).rsplit('#', maxsplit=1)[0]
    return name, namespace


def get_ontology_properties(g: Graph) -> dict:
    """
    Given a graph that has been loaded with a single ontology file it retrieves 
    all the informational elements about the ontology via its properties in a
    dict structure:

    {
        title: "..."
    }
    """
    ontology_uri = g.value(predicate=RDF.type, object=OWL.Ontology)
    ontology_name, ontology_namespace = parse_uri_ref(ontology_uri)
    if DEBUG:
        print(f"Detected Ontology --> {ontology_name}")
    ontology = dict(
        title=str(g.value(subject=ontology_uri, predicate=DC.title)),
        name=ontology_name,
        uri=str(ontology_uri),
        versionInfo=str(g.value(subject=ontology_uri, predicate=OWL.versionInfo)),
        publisher=str(g.value(subject=ontology_uri, predicate=DC.publisher)),
        term_status=str(g.value(subject=ontology_uri, predicate=VS.term_status)),
        description=str(g.value(subject=ontology_uri, predicate=DC.description)),
        creators=[]
    )

    # Adds the list of the creators to the Ontology Dictionary
    for (_, _, o) in g.triples((ontology_uri, DC.creator, None)):
        creator_name, _ = parse_uri_ref(o)
        ontology["creators"].append(creator_name)
    return ontology


def get_children_objects(g: Graph, subject: URIRef, relationship_type: URIRef) -> list:
    """
    """
    children = []
    for (s, _, _) in g.triples((None, relationship_type, subject)):
        child_name, child_namespace = parse_uri_ref(s)
        if relationship_type == RDFS.domain:
            if (s, RDF.type, OWL.DatatypeProperty) in g:
                child_type = OWL.DatatypeProperty
            elif (s, RDF.type, OWL.ObjectProperty) in g:
                child_type = OWL.ObjectProperty
        else:
            child_type = g.value(s, RDF.type, None)
        
        child_type_name, _ = parse_uri_ref(child_type)

        sc = dict(
            name=child_name,
            description=str(g.value(subject=s, predicate=DC.description)),
            namespace=child_namespace,
            uri=str(s),
            type_name=child_type_name,
            type_uri=child_type
        )

        if child_type in [OWL.DatatypeProperty, OWL.ObjectProperty]:
            domain_uri = g.value(subject=s, predicate=RDFS.domain)
            domain_name, _ = parse_uri_ref(domain_uri)

            range_uri = g.value(subject=s, predicate=RDFS.range)
            range_name, _ = parse_uri_ref(range_uri)

            sc["domain_name"] = domain_name
            sc["domain_uri"] = domain_uri
            sc["range_name"] = range_name
            sc["range_uri"] = range_uri

        children.append(sc)
    return sorted(children, key=lambda k: k['name'])


def get_class_instance_data_props(g: Graph, i: dict) -> list:
    """
    """
    props = []
    for (_, p, o) in g.triples((URIRef(i["uri"]), None, None)):
        if p != RDF.type:
            property_name, _ = parse_uri_ref(p)
            data_prop = {
                "name": property_name,
                "value": o
            }
            props.append(data_prop)
    return props


def get_class_instances(g: Graph, class_uri: URIRef) -> list:
    """
    """
    instances = []
    for (s, _, _) in g.triples((None, RDF.type, class_uri)):
        instance_name, instance_namespace = parse_uri_ref(s)
        if "http" in instance_namespace:
            i = dict (
                name=instance_name,
                namespace=instance_namespace,
                uri=str(s),
                description=str(g.value(subject=s, predicate=DC.description))
            )
            i["data_properties"] = get_class_instance_data_props(g, i)
            instances.append(i)
    return sorted(instances, key=lambda k: k['name'])


def get_classes(g: Graph) -> list:
    """
    """
    ontology_uri = g.value(predicate=RDF.type, object=OWL.Ontology)
    _, ontology_namespace = parse_uri_ref(ontology_uri)

    classes = []
    for (s, _, _) in g.triples((None, RDF.type, OWL.Class)):
        class_name, class_namespace = parse_uri_ref(s)
        external = class_namespace != ontology_namespace
        subclasses = get_children_objects(g=g, subject=s, relationship_type=RDFS.subClassOf)
        properties = get_children_objects(g=g, subject=s, relationship_type=RDFS.domain)
        ranges_of = get_children_objects(g=g, subject=s, relationship_type=RDFS.range)
        class_instances = get_class_instances(g, s)
        if "http" in class_namespace:
            c = dict(
                name=class_name,
                namespace=class_namespace,
                uri=str(s),
                description=str(g.value(subject=s, predicate=DC.description)),
                subclasses=subclasses,
                properties=properties,
                ranges_of=ranges_of,
                superclass=str(g.value(subject=s, predicate=RDFS.subClassOf))\
                    .rsplit('#', maxsplit=1)[-1],
                external=external,
                instances=class_instances
            )
            classes.append(c)
    return sorted(classes, key=lambda k: k['name'])


def get_properties(classes: list) -> list:
    """
    """
    properties = []
    for c in classes:
        for p in c["properties"]:
            properties.append(p)
    return properties


def render_template(ontology: dict, ontology_image: str) -> None:
    env = Environment(loader=PackageLoader('sprowl', 'templates'))
    template = env.get_template('enhanced.html')  # Use enhanced template by default
    cl = [
            {"name" : c["name"],
                "namespace": c["namespace"],
                "uri": c["uri"],
                "description": c["description"],
                "superclass": c["superclass"],
                "external": c["external"],
                "instances": c["instances"]
            } for c in ontology["classes"]]
    classes_json = json.dumps(cl)

    properties_json = json.dumps([p for p in ontology["properties"] if p["type_name"] == "ObjectProperty"])
    data_properties_json = json.dumps([{"name": p["name"], "domain_name": p["domain_name"]} for p in ontology["properties"] if p["type_name"] == "DatatypeProperty"])

    subcl = [{
        "child": s["name"],
        "parent": c["name"]
    } for c in ontology["classes"] for s in c["subclasses"]]
    subclass_properties_json = json.dumps(subcl)

    html_output = template.render(
        ontology=ontology,
        classes=ontology["classes"],
        classes_json=classes_json,
        properties=ontology["properties"],
        properties_json=properties_json,
        data_properties_json=data_properties_json,
        subclass_properties_json=subclass_properties_json,
        image=ontology_image
    )

    output_filename = ontology["name"]
    output_filename = CONTAINER_DIR + output_filename + ".html"
    if DEBUG:
        print(f"Saving to --> {output_filename}")
    text_file = open(output_filename, "w", encoding="utf-8")
    text_file.write(html_output)
    text_file.close()


def load_ontology(file_location: str) -> Graph:
    try:
        g_location = file_location
        g = Graph()
        g.parse(g_location)
    except ValueError as error:
        print(f"Error: {error}")
        sys.exit(-1)
    return g


def prepare_file(orig_file: str, destination_dir: str, destination_name: str) -> str:
    destination_filename = None
    if orig_file is not None:
        _, extension = os.path.splitext(orig_file)
        destination_filename = destination_dir + destination_name + extension
        copyfile(orig_file, CONTAINER_DIR + destination_filename)
    return str(destination_filename)


def debug_checK_thing(g: Graph, thing: str) -> None:
    """
    Debug only function to print all the statements where 'thing' appears in the
    graph as a subject, predicate or object
    """
    ontology_uri = g.value(predicate=RDF.type, object=OWL.Ontology)
    _, ontology_namespace = parse_uri_ref(ontology_uri)
    u = URIRef(ontology_namespace + "#" + thing)
    print(f"---------> Checking thing: {thing}")
    print("=== SUBJECT ===")
    for (s, p, o) in g.triples((u, None, None)):
        print(f"{s} {p} {o}")
    print("=== PREDICATE ===")
    for (s, p, o) in g.triples((None, u, None)):
        print(f"{s} {p} {o}")
    print("=== OBJECT ===")
    for (s, p, o) in g.triples((None, None, u)):
        print(f"{s} {p} {o}")
    print(f"--------->  End of Thing: {thing}")


def main(ontology_input_file, ontology_input_image):
    g = load_ontology(ontology_input_file)
    ontology = get_ontology_properties(g)
    ontology["download_location"] = prepare_file (
        ontology_input_file,
        RESOURCE_DIR,
        ontology["name"])
    ontology["classes"] = get_classes(g)
    ontology["properties"] = get_properties(ontology["classes"])

    if DEBUG:
        title = ontology["title"]
        print(f"Parsing Ontology --> {title}")

    ontology_image = prepare_file(ontology_input_image, IMAGE_DIR, ontology["name"])
    render_template(ontology, ontology_image)


@route('/')
def index():
    filename = 'data-engineering.html'
    return static_file(filename, root='./ontologies')

@route('/favicon.ico')
@route('/static/favicon.svg')
def serve_favicon():
    return static_file('favicon.svg', root='./ontologies/static')

@route('/theme/<cssFile>')
def serve_css_files(cssFile):
    file_path = './ontologies/theme'
    return static_file(cssFile, file_path)


@route('/css/<cssFile>')
def serve_vss_files_enhanced(cssFile):
    file_path = './ontologies/css'
    return static_file(cssFile, file_path)


@route('/js/<jsFile>')
def serve_js_files(jsFile):
    file_path = './ontologies/js/'
    return static_file(jsFile, file_path)

@route('/js/mxGraph/<jsFile>')
def serve_mxgraph_files(jsFile):
    file_path = './ontologies/js/mxgraph-4.2.2/javascript/'
    return static_file(jsFile, file_path)

@route('/resources/<resFile>')
def serve_res_files(resFile):
    file_path = './ontologies/js/mxgraph-4.2.2/javascript/src/resources/'
    return static_file(resFile, file_path)


def to_file(file, img):
    main(file, img)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SprOWL3 - Ontology Auto-Documenter")
    parser.add_argument('-d', '--debug', help="Displays debug messsages", action="store_true")
    parser.add_argument('-f', '--file', help="The ontology file to document", action="store")
    parser.add_argument('-i', '--image', help="The ontology image file to add to the documentation", action="store")
    parser.add_argument('-w', '--web', help="runs a web server to display the output instead of saving it to a file.", action="store_true")

    try:
        if len(sys.argv) < 2:
            raise ValueError("No arguments passed")
        args = parser.parse_args()
    except ValueError as err:
        print(f"Error: {err}\n")
        parser.print_help()
        sys.exit(0)
    
    if args.debug:
        DEBUG = True
        print("SprOWL3 - Ontology Auto-Documenter - CVR Data Consulting Services.")
        print("- Debug Mode ON\n")

        img = None

        to_file(args.file, img)
        if args.web:
            run(host='localhost', port=8181)

# TODO: Extract definitions to Excel