import re
import typing
import pydotplus
import bs4

from lxml import etree
from dateutil import parser


def set_graph_options(net, output_path):
    options_str = (
        """var options = {
            "nodes": {
                "scaling": {
                    "min": 10,
                    "max": 30
                },
                "font": {
                    "size": 12,
                    "face": "Tahoma",
                },
            },
            "edges": {
                "smooth": {
                    "type": "continuous"
                },
                "arrows": {
                  "to": {
                    "enabled": true,
                    "scaleFactor": 0.45
                    }
                }
            },
            "layout": {
                "hierarchical": {
                    "enabled": true,
                    "levelSeparation": -150,
                    "sortMethod": "directed"
                }
            },
            "physics": {
                "minVelocity": 0.75,
                "solver": "hierarchicalRepulsion",
                "hierarchicalRepulsion": {
                    "avoidOverlap": 1,
                    "nodeDistance": 175,
                    "damping": 0.15
                },
                "timestep": 0.5,
                "stabilization": {
                    "enabled": true,
                }
            }
        };"""
    )
    net_html_match = re.search(r'var options = {.*};', net.html, flags=re.DOTALL)
    if net_html_match is not None:
        net.html = net.html.replace(net_html_match.group(0), options_str)

    with open(output_path, "w+") as out:
        out.write(net.html)


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


def add_js_click_functionality(net, output_path, graph_ttl_stream=None):
    f_process_binding = '''
        function process_binding(binding) {
            let subj_id = binding.subject.id ? binding.subject.id : binding.subject.value;
            let obj_id = binding.object.id ? binding.object.id : binding.object.value;
            let edge_id = subj_id + "_" + obj_id;
            
            subj_node = {
                id: subj_id,
                label: binding.subject.value ? binding.subject.value : binding.subject.id,
                clickable: true,
                font: {
                      'multi': "html",
                      'face': "courier"
                     }
            }
            edge_obj = {
                id: edge_id,
                from: subj_id,
                to: obj_id,
                title: binding.predicate.value
            }
            obj_node = {
                id: obj_id,
                label: binding.object.value ? binding.object.value : binding.object.id,
                clickable: true,
                font: {
                      'multi': "html",
                      'face': "courier"
                     }
            }
            if(!nodes.get(subj_id)) {
                nodes.add([subj_node]); 
                network.fit();
            }
            if(binding.predicate.value.endsWith('#type')) {
                
                idx_slash = obj_id.lastIndexOf("/");
                substr_q = obj_id.slice(idx_slash + 1); 
                if (substr_q) {
                    idx_hash = substr_q.indexOf("#");
                    if (idx_hash)
                      type_name = substr_q.slice(idx_hash + 1); 
                }
                subj_node_to_update = nodes.get(subj_id);
                if(!subj_node_to_update['type']) {
                    subj_node_to_update['label'] = '<b>' + subj_node_to_update['label'] + '</b>\\n' + type_name
                    nodes.update({ id: subj_id, 
                                    label: subj_node_to_update['label'],
                                    type: type_name });
                }
            }
            else {
                if(!edges.get(edge_id)) {
                    edges.add([edge_obj]);
                }
                if(!nodes.get(obj_id)) {
                    nodes.add(obj_node);
                    network.fit();
                        if(binding.object.termType === "Literal") {
                        // disable click for any literal node
                        nodes.update({ id: obj_id, clickable: false });
                    }
                }
            }
        }
        
        function drawGraph() {
    '''

    f_draw_graph = f'''
     
        const parser = new N3.Parser({{ format: 'ttl' }});
        const n3_utils = N3.Util;
        let prefix_processing;
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
                    store.addQuad(triple.subject, triple.predicate, triple.object);
                }}
            }}
        );
        
        network.on("stabilized", function (e) {{
            network.setOptions( {{ "physics": {{ enabled: false }} }} );
            console.log("physics deactivated");
        }});
        
        network.on("click", function(e) {{
            if(e.nodes[0]) {{
                selected_node = nodes.get(e.nodes[0]);
                if (selected_node && selected_node['clickable']) {{
                    
                    network.setOptions( {{ 
                        "physics": {{ 
                            "minVelocity": 0.75,
                            "solver": "hierarchicalRepulsion",
                            "hierarchicalRepulsion": {{
                                "avoidOverlap": 0.9,
                                "nodeDistance": 175,
                                "damping": 0.15
                            }},
                            "timestep": 0.5,
                            "stabilization": {{
                                "enabled": true,
                            }}
                        }} 
                    }} );
                    console.log("physics reactivated");
                    
                    myEngine.queryQuads(
                        `CONSTRUCT {{
                            <` + selected_node.id + `> ?p ?o .
                            ?o a ?o_type . 
                        }}
                        WHERE {{
                             {{ <` + selected_node.id + `> ?p ?o . }}
                            UNION
                            {{
                                <` + selected_node.id + `> ?p ?o .
                                ?o a ?o_type . 
                            }}
                        }}`,
                    {{
                        sources: [ store ]
                    }}
                ).then(
                    function (bindingsStream) {{
                        // Consume results as a stream (best performance), alternative with array exists
                        bindingsStream.on('data', (binding) => {{
                            process_binding(binding);
                        }});
                        bindingsStream.on('end', () => {{
                            // The data-listener will not be called anymore once we get here.
                            // console.log('end\\n');
                        }});
                        bindingsStream.on('error', (error) => {{
                            console.error("error when clicked a node: " + error);
                        }});
                    }}
                );
            }}
            }}
        }});
        
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
                process_binding(binding);
            }});
            bindingsStreamCall.on('end', () => {{
            }});
            bindingsStreamCall.on('error', (error) => {{ 
                console.error(error);
            }});
        }})();
        
        var container_configure = document.getElementsByClassName("vis-configuration-wrapper");
        if(container_configure && container_configure.length > 0) {{
            container_configure = container_configure[0];
            container_configure.style = {{}};
            container_configure.style.height="300px";
            container_configure.style.overflow="scroll";
        }}
        
        return network;
    }}
    '''
    net_html_match = re.search(r'return network;.*}', net.html, flags=re.DOTALL)
    if net_html_match is not None:
        net.html = net.html.replace(net_html_match.group(0), f_draw_graph)

    net_html_match = re.search(r'function drawGraph\(\) {', net.html, flags=re.DOTALL)
    if net_html_match is not None:
        net.html = net.html.replace(net_html_match.group(0), f_process_binding)

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
