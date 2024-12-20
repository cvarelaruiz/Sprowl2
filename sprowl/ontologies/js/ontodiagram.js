class OntologyDiagram {
    constructor(GraphName, containerElement, outlineContainerElementID) {
        this.container = containerElement;
        this.GraphName = GraphName;
        this.model = new mxGraphModel();
        this.graph = new mxGraph(this.container, this.model);
        this.graph.setResizeContainer(true);
        this.parent = this.graph.getDefaultParent();

        // Disables edges to be disconnected from their termninals
        this.graph.setDisconnectOnMove(false);

        this.graph.setPanning(true);
        this.graph.centerZoom = false;
        this.graph.panningHandler.useLeftButtonForPanning = true;
        this.graph.panningHandler.popupMenuHandler = false;

        this.outlineElement = document.getElementById(outlineContainerElementID);
        this.outine = new mxOutline(this.graph, this.outlineElement);
        mxEvent.disableContextMenu(containerElement);

        this.graph.setEnabled(true);
        this.layout = new mxFastOrganicLayout(this.graph);
        this.layout.maintainParentLocation = true;

        // Configure the layout
        this.layout.forceConstant = 80; //Higher value means more space between vertices
        this.layout.minDistanceLimit = 2; // Minimum distance between vertices
        this.layout.maxDistanceLimit = 500; // Maximum distance between vertices
        this.layout.initialTemp = 200; // Initial 'temperature' for the layout algorithm

        // Creates a new layout manager and sets the default layout
        this.layoutManager = new mxLayoutManager(this.graph);
        this.layoutManager.defaultLayout = this.layout;

        // Define the style for circular vertices
        var circleStyle = new Object();
        circleStyle[mxConstants.STYLE_SHAPE] = mxConstants.SHAPE_ELLIPSE;
        circleStyle[mxConstants.STYLE_PERIMETER] = mxPerimeter.EllipsePerimeter;
        this.graph.getStylesheet().putCellStyle('circleStyle', circleStyle);

        //Define the syt;e for rectangular vertices
        var rectangularSyle = new Object();
        rectangularSyle[mxConstants.STYLE_SHAPE] = mxConstants.SHAPE_RECTANGLE;
        rectangularSyle[mxConstants.STYLE_PERIMETER] = mxPerimeter.RectangularPerimter;
        rectangularSyle[mxConstants.STYLE_AUTOSIZE] = 1; //Autosize the verticales
        this.graph.getStylesheet().putCellStyle('rectangularStyle', rectangularSyle);

        this.object_styles = {
            "ontology_class_style": "fillColor=#A8CCFF;strokeColor=#000000;strokeWidth=1;shadow=1;rounded=1;arcSize=50;whiteSpace=wrap;fontColor=#000000;circleStyle=1;",
            "ontology_class_external_style": "fillColor=#3666CB;strokeColor=#000000;strokeWidth=1;shadow=1;rounded=1;arcSize=50;whiteSpace=wrap;fontColor=#000000;",
            "edge_style": "fillColor=#000000;strokeColor=#000000;strokeWidth=2;verticalAlign=top;",
            "subclass_edge_style": "fillColor=#000000;strokeColor=#000000;strokeWidth=2;verticalAlign=top;dashed=1;",
            "data_property_style": "fillColor=#33cc33;strokeColor=#000000;strokeWidth=1;shadow=1;fontColor=#000000;rectangleStyle=1;whiteSpace=wrap;spacing=5;"
        }

        this.classes = {};
        this.relationships = {};
    }

    beginUpdate() {
        this.model.beginUpdate();
    }

    executeLayout() {
        this.model.endUpdate();
        this.layout.execute(this.graph.getDefaultParent());
    }

    refreshLayout() {
        this.graph.refresh();
    }

    addOntologyClass(className, classURI, classDescription, superClass, external) {
        if (!(className in this.classes)) {
            if (external) {
                var style = this.object_styles["ontology_class_external_style"];
            } else {
                var style = this.object_styles["ontology_class_style"];
            }
            var vertex = this.graph.insertVertex(this.parent, null, className, 0, 0, 60, 60, style);
            vertex.setConnectable(true);
            vertex.setVertex(true);

            this.classes[className] = vertex;
            return vertex;
        } else {
            return this.classes[className];
        }
    };

    Connect(srcName, destName, label, style) {
        var src = this.classes[srcName];
        var dst = this.classes[destName];
        var style = this.object_styles[style];

        var edge = this.graph.insertEdge(this.parent, null, label, src, dst, style);

        // Check if a reciprocal edge exists and offset the labels so they're readable
        var reciprocalEdges = this.graph.getModel().getEdgesBetween(dst, src, false);
        if (reciprocalEdges.length > 0) {
            var reciprocalEdge = reciprocalEdges[0];

            var geo_recriprocal = this.graph.getCellGeometry(reciprocalEdge);
            geo_recriprocal.offset = new mxPoint(20, 30);
            this.graph.getModel().setGeometry(reciprocalEdge, geo_recriprocal);

            var geo = this.graph.getCellGeometry(edge);
            geo.offset = new mxPoint(-20, -30);
            this.graph.getModel().setGeometry(edge, geo);
        }

        return edge;
    };

    addDataProperty(className, propertyName) {
        if (className in this.classes) {

            var style = this.object_styles["data_property_style"];
            var dataPropertyVertex = this.graph.insertVertex(this.parent, null, propertyName, 0, 0, 80, 30, style);
            dataPropertyVertex.setConnectable(true);
            dataPropertyVertex.setVertex(true);
            this.graph.updateCellSize(dataPropertyVertex);
            this.graph.insertEdge(this.parent, null, '', this.classes[className], dataPropertyVertex, this.object_styles["edge_style"]);
            return dataPropertyVertex;
        }
        return null;
    }

    // enableToolbar(menuContainerElementID, static_path) {
    //     var menuElement = document.getElementById(menuContainerElementID);
    //     menuElement.style.padding = '4px';

    //     var tb = new mxToolbar(menuElement);
    //     tb.addItem('Zoom In', static_path + 'zoom_in32.png', function (evt) {
    //         this.graph.zoomIn();
    //     }.bind(this));

    //     tb.addItem('Zoom Out', static_path + 'zoom_out32.png', function (evt) {
    //         this.graph.zoomOut();
    //     }.bind(this));

    //     tb.addItem('Actual Size', static_path + 'view_1_132.png', function (evt) {
    //         this.graph.zoomActual();
    //     }.bind(this));

    //     tb.addItem('Toggle Outline', static_path + 'map.png', function (evt) {
    //         this.toggleOutline();
    //     }.bind(this));

    //     tb.addItem('Save as draw.io Diagram', static_path + 'save.png', function (evt) {
    //         this.exportGraph();
    //     }.bind(this));

    //     tb.addItem('Print', static_path + 'print32.png', function (evt) {
    //         var preview = new mxPrintPreview(this.graph, 1);
    //         preview.open();
    //     }.bind(this));

    //     tb.addItem('Poster Print', static_path + 'press32.png', function (evt) {
    //         var pageCount = mxUtils.prompt('Enter Max Page Count', '1');
    //         if (pageCount != null) {
    //             var scale = mxUtils.getScaleForPageCount(pageCount, this.graph);
    //             var preview = new mxPrintPreview(this.graph, scale);
    //             preview.open();
    //         }
    //     }.bind(this));
    // };

    // toggleOutline() {
    //     if (this.outlineElement.style.display == 'none')
    //         this.outlineElement.style.display = 'block';
    //     else
    //         this.outlineElement.style.display = 'none';
    // };

    exportGraph() {
        var encoder = new mxCodec();
        var node = encoder.encode(this.graph.getModel());
        var xml_data = mxUtils.getPrettyXml(node);

        var a = window.document.createElement('a');
        a.href = window.URL.createObjectURL(new Blob([xml_data], { type: 'type/xml' }));
        a.download = this.GraphName + ' Ontology.xml';

        // Append anchor to body
        document.body.appendChild(a);
        a.click();

        // Remove anchor from body
        document.body.removeChild(a);
    };
}

//define new function callable from the outside
function ComposeDiagram(ontology_title, ontology_classes, ontology_properties, data_properties, subclass_properties, graph_container, outlineContainer) {
    var g = new OntologyDiagram(ontology_title, graph_container, outlineContainer);
    g.beginUpdate();
    try {
        // Add classes to the diagram
        for (var ontology_class of ontology_classes) {
            g.addOntologyClass(ontology_class['name'], ontology_class['uri'], '', '', ontology_class['external']);
        }

        // Add main relationships to the diagram
        for (var ontology_property of ontology_properties) {
            g.Connect(ontology_property['domain_name'], ontology_property['range_name'], ontology_property['name'], 'edge_style');
        }

        // Add subclass relationships
        for (var subclass_property of subclass_properties) {
            g.Connect(subclass_property['child'], subclass_property['parent'], 'subclass of', 'subclass_edge_style');
        }

        // Add data properties
        for (var data_property of data_properties) {
            g.addDataProperty(data_property['domain_name'], data_property['name']);
        }
    } finally {
        g.executeLayout();
        g.refreshLayout();
    }
    return g;
};