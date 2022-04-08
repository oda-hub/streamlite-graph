import typing
import pydotplus
import bs4

from lxml import etree
from dateutil import parser


def set_graph_options(graph):
    graph.set_options(
        """{
            "physics": {
                "hierarchicalRepulsion": {
                    "nodeDistance": 175,
                    "damping": 0.15
                },
                "minVelocity": 0.75,
                "solver": "hierarchicalRepulsion"
            },
            "configure": {
                "filter": ""
            },
            "layout": {
                "hierarchical": {
                    "enabled": true,
                    "levelSeparation": -150,
                    "sortMethod": "directed"
                }
            },
            "nodes": {
                "scaling": {
                  "min": 10,
                  "max": 100,
                  "label": {
                    "enabled": true
                  }
                },
                "labelHighlightBold": true
            },
            "edges": {
                "arrows": {
                  "to": {
                    "enabled": true,
                    "scaleFactor": 0.45
                    }
                },
                "arrowStrikethrough": true,
                "color": {
                    "inherit": true
                },
                "physics": false,
                "smooth": false
            }
        }"""
    )


def get_node_graphical_info(node: typing.Union[pydotplus.Node],
                   type_node) -> [str, str]:
    node_label = ""
    node_title = ""
    if 'label' in node.obj_dict['attributes']:
        # parse the whole node table into a lxml object
        table_html = etree.fromstring(node.get_label()[1:-1])
        tr_list = table_html.findall('tr')
        for tr in tr_list:
            list_td = tr.findall('td')
            if len(list_td) == 2:
                list_left_column_element = list_td[0].text.split(':')
                # setting label
                if type_node == 'Action':
                    if 'command' in list_left_column_element:
                        node_label = '<b>' + list_td[1].text[1:-1] + '</b>'
                elif type_node == 'CommandInput':
                    node_label = '<b><i>' + list_td[1].text[1:-1] + '</i></b>'
                else:
                    node_label = ('<b>' + type_node + '</b>\n' + list_td[1].text[1:-1])
                # setting title
                if 'startedAtTime' in list_left_column_element:
                    parsed_startedAt_time = parser.parse(list_td[1].text.replace('^^xsd:dateTime', '')[1:-1])
                    # create an additional row to attach at the bottom, so that time is always at the bottom
                    node_title += parsed_startedAt_time.strftime('%Y-%m-%d %H:%M:%S') + '\n'

    if node_label == "":
        node_label = '<b>' + type_node + '</b>'
    if node_title == "":
        node_title = type_node
    return node_label, node_title


def get_id_node(node: typing.Union[pydotplus.Node]) -> str:
    id_node = None
    if 'label' in node.obj_dict['attributes']:
        table_html = etree.fromstring(node.get_label()[1:-1])
        tr_list = table_html.findall('tr')

        td_list_first_row = tr_list[0].findall('td')
        if td_list_first_row is not None:
            b_element_title = td_list_first_row[0].findall('B')
            if b_element_title is not None:
                id_node = b_element_title[0].text

    return id_node


def get_edge_label(edge: typing.Union[pydotplus.Edge]) -> str:
    edge_label = None
    if 'label' in edge.obj_dict['attributes']:
        edge_html = etree.fromstring(edge.obj_dict['attributes']['label'][1:-1])
        edge_label_list = edge_html.text.split(":")
        if len(edge_label_list) == 1:
            edge_label = edge_html.text.split(":")[0]
        else:
            edge_label = edge_html.text.split(":")[1]
    return edge_label


def add_js_click_functionality(net, output_path, hidden_nodes_dic, hidden_edges_dic, graph_ttl_stream=None):
    f_click = f'''
     
    const parser = new N3.Parser({{ format: 'ttl' }}); 
    let store = new N3.Store();
    let quad_list = [];
    const myEngine = new Comunica.QueryEngine();
    parsed_graph = parser.parse(`{graph_ttl_stream}`,
        function (error, triple, prefixes) {{
            // Always log errors
            if (error) {{
                console.error(error);
            }}
            if (triple) {{
                // console.log(triple);
                store.addQuad(triple.subject, triple.predicate, triple.object);
            }}
        }}
    );
    
    (async() => {{
        const bindingsStreamCall = await myEngine.queryQuads(
            `CONSTRUCT {{
                ?action a <http://schema.org/Action> ;
                    <https://swissdatasciencecenter.github.io/renku-ontology#command> ?actionCommand .
        
                ?activity a ?activityType ;
                    <http://www.w3.org/ns/prov#startedAtTime> ?activityTime ;
                    <http://www.w3.org/ns/prov#qualifiedAssociation> ?activity_qualified_association .
    
                ?activity_qualified_association <http://www.w3.org/ns/prov#hadPlan> ?action .
            }}
            WHERE {{ 
                ?action a <http://schema.org/Action> ;
                    <https://swissdatasciencecenter.github.io/renku-ontology#command> ?actionCommand .
                     
                ?activity a ?activityType ;
                    <http://www.w3.org/ns/prov#startedAtTime> ?activityTime ;
                    <http://www.w3.org/ns/prov#qualifiedAssociation> ?activity_qualified_association .
                
                ?activity_qualified_association <http://www.w3.org/ns/prov#hadPlan> ?action .
            }} `,
            {{
                sources: [ store ] 
            }}
        ); 
        bindingsStreamCall.on('data', (binding) => {{
            let subj_id = binding.subject.id ? binding.subject.id : binding.subject.value;
            // subj_id = subj_id.replaceAll('"', '');
            let obj_id = binding.object.id ? binding.object.id : binding.object.value;
            // obj_id = obj_id.replaceAll('"', '');
            let edge_id = subj_id + "_" + obj_id;
            
            subj_node = {{
                id: subj_id,
                label: binding.subject.value ? binding.subject.value : binding.subject.id,
                title: binding.subject.value ? binding.subject.value : binding.subject.id,
                font: {{
                      'multi': "html",
                      'face': "courier"
                     }}
            }}
            obj_node = {{
                id: obj_id,
                label: binding.object.value ? binding.object.value : binding.object.id,
                title: binding.object.value ? binding.object.value : binding.object.id,
                font: {{
                      'multi': "html",
                      'face': "courier"
                     }}
            }}
            if(!nodes.get(subj_id)) {{
                nodes.add([subj_node]); 
            }}
            if(binding.predicate.value.endsWith('#type')) {{
                subj_node_to_update = nodes.get(subj_id);
                subj_node_to_update['label'] = '<b>' + subj_node_to_update['label'] + '</b>\\n' + obj_node['label']
                nodes.update({{ id: subj_id, label: subj_node_to_update['label'] }});
            }}
            else if(obj_node.id[0] === '"') {{
                subj_node_to_update = nodes.get(subj_id);
                subj_node_to_update['label'] = subj_node_to_update['label'] + '\\n' + obj_node['id']
                nodes.update({{ id: subj_id, label: subj_node_to_update['label'] }});
            }}
            else {{
                if(!edges.get(edge_id)) {{
                    edges.add([
                        {{
                            id: edge_id,
                            from: subj_id,
                            to: obj_id,
                            title: binding.predicate.value,
                            hidden: false 
                        }}
                    ]);
                }}
                if(!nodes.get(obj_id)) {{
                    nodes.add(obj_node);
                }}
            }}
        }});
        
        bindingsStreamCall.on('end', () => {{
            // The data-listener will not be called anymore once we get here.
            // console.log('end\\n');
            // console.log(nodes.get());
        }});
        bindingsStreamCall.on('error', (error) => {{ 
            console.error(error);
        }});
    }})();
    
    var toggle = false;
    network.on("click", function(e) {{
        if(e.nodes[0]) {{
            selected_node = nodes.get(e.nodes[0]);
            console.log(selected_node.id);
            if (selected_node) {{
                 myEngine.queryQuads(
                    `CONSTRUCT {{
                        <` + selected_node.id + `> ?p ?o .
                        ?o a ?o_type . 
                    }}
                    WHERE {{
                        <` + selected_node.id + `> ?p ?o .
                        ?o a ?o_type . 
                    }}`,
                {{
                    sources: [ store ]
                }}
            ).then(
                function (bindingsStream) {{
                    // Consume results as a stream (best performance)
                    bindingsStream.on('data', (binding) => {{
                        console.log(binding);
                        // Obtaining values
                        let subj_id = binding.subject.id ? binding.subject.id : binding.subject.value;
                        let obj_id = binding.object.id ? binding.object.id : binding.object.value;
                        let edge_id = subj_id + "_" + obj_id;
                        subj_node = {{
                            id: subj_id,
                            label: binding.subject.value ? binding.subject.value : binding.subject.id,
                            title: binding.subject.value ? binding.subject.value : binding.subject.id,
                            font: {{
                                  'multi': "html",
                                  'face': "courier"
                                 }}
                        }}
                        obj_node = {{
                            id: obj_id,
                            label: binding.object.value ? binding.object.value : binding.object.id,
                            title: binding.object.value ? binding.object.value : binding.object.id,
                            font: {{
                                  'multi': "html",
                                  'face': "courier"
                                 }}
                        }}
                        
                        if(!nodes.get(subj_id)) {{
                            nodes.add(subj_node); 
                        }}
                        if(binding.predicate.value.endsWith('type')) {{
                            nodes.update({{ id: subj_node['id'], label: '<b>' + subj_node['label'] + '</b>\\n' + obj_node['label'] }})
                        }} else {{
                            if(!edges.get(edge_id)) {{
                                edges.add([
                                    {{
                                        id: edge_id,
                                        from: subj_id,
                                        to: obj_id,
                                        title: binding.predicate.value,
                                        hidden: false 
                                    }}
                                ]);
                            }}
                            if(!nodes.get(obj_id)) {{
                                nodes.add([obj_node]);
                            }}
                        }}
                    }});
                    bindingsStream.on('end', () => {{
                        // The data-listener will not be called anymore once we get here.
                        // console.log('end');
                    }});
                    bindingsStream.on('error', (error) => {{
                        console.error("error when clicked a node: " + error);
                    }});
                }}
            );
        }}
        }}
    }});
    
    var container_configure = document.getElementsByClassName("vis-configuration-wrapper");
    if(container_configure && container_configure.length > 0) {{
        container_configure = container_configure[0];
        container_configure.style = {{}};
        container_configure.style.height="300px";
        container_configure.style.overflow="scroll";
    }}
    return network;
    '''

    net.html = net.html.replace('return network;', f_click)

    with open(output_path, "w+") as out:
        out.write(net.html)


def update_js_libraries(html_fn):
    # let's patch the template
    # load the file
    with open(html_fn) as template:
        html_code = template.read()
        soup = bs4.BeautifulSoup(html_code, "html.parser")

    soup.head.link.decompose()
    soup.head.script.decompose()

    new_script_updated_vis_library = soup.new_tag("script", type="application/javascript",
                              src="https://unpkg.com/vis-network/standalone/umd/vis-network.js")
    soup.head.append(new_script_updated_vis_library)

    new_script_rdflib_library = soup.new_tag("script", type="application/javascript",
                              src="https://unpkg.com/n3/browser/n3.min.js")
    soup.head.append(new_script_rdflib_library)

    new_script_query_sparql_library = soup.new_tag("script", type="application/javascript",
                                             src="http://rdf.js.org/comunica-browser/versions/latest"
                                                 "/engines/query-sparql-rdfjs/comunica-browser.js")
    soup.head.append(new_script_query_sparql_library)

    # save the file again
    with open(html_fn, "w") as outf:
        outf.write(str(soup))
