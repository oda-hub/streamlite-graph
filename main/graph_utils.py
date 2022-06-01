import re
import typing
import pydotplus
import bs4

from lxml import etree
from dateutil import parser


def set_graph_options(net, output_path):
    options_str = (
        """
        options_repulsion = {
            "autoResize": true,
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
                    "scaleFactor": 0.55
                    }
                }
            },
            "layout": {
                "hierarchical": {
                    "enabled": false
                }
            },
            "physics": {
                "enabled": true,
                "minVelocity": 1,
                "maxVelocity": 15,
                "solver": "repulsion",
                "repulsion": {
                    "nodeDistance": 200
                },
                "stabilization": {
                    "enabled": true,
                    "iterations": 10
                },
            }
        };
        
        options_hierarchical = {
            "autoResize": true,
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
                    "scaleFactor": 0.55
                    }
                }
            },
            "layout": {
                "hierarchical": {
                    "enabled": true,
                    "levelSeparation": -150,
                    "sortMethod": "directed",
                    "nodeSpacing": 150
                }
            },
            "physics": {
                "enabled": true,
                "minVelocity": 1,
                "maxVelocity": 15,
                "solver": "hierarchicalRepulsion",
                "hierarchicalRepulsion": {
                    "nodeDistance": 175,
                    "damping": 0.15
                },
                "stabilization": {
                    "enabled": true,
                    "iterations": 10
                },
            }
        };
        
        var options = {
            "autoResize": true,
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
                    "scaleFactor": 0.55
                    }
                }
            },
            "layout": {
                "hierarchical": {
                    "enabled": false
                }
            },
            "physics": {
                "enabled": true,
                "minVelocity": 1,
                "maxVelocity": 15,
                "solver": "repulsion",
                "stabilization": {
                    "enabled": true,
                    "iterations": 10
                },
                "repulsion": {
                    "nodeDistance": 200
                },
            }
        };
        
        """
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


def set_html_content(net, output_path, graph_config_names_list=None):
    html_code = '''
        <div style="margin: 5px 0px 15px 5px"><button type="button" onclick="reset_graph()">Reset graph!</button></div>
        
        <div style="margin: 15px 0px 10px 5px; font-weight: bold;">Change graph layout</div>
        
        <div style="margin: 5px">
            <label><input type="radio" id="repulsion_layout" name="graph_layout" value="repulsion" onchange="apply_layout(this)" checked>
            Random</label>
        </div>
        <div style="margin: 5px">
            <label><input type="radio" id="hierarchical_layout" name="graph_layout" value="hierarchicalRepulsion" onchange="apply_layout(this)" unchecked>
            Hierarchical</label>
        </div>
        
        <div style="margin: 15px 0px 10px 5px; font-weight: bold;">Enable/disable selections for the graph</div>
        
        <div style="margin: 5px">
            <label><input type="checkbox" id="oda_filter" value="oda, odas" onchange="enable_filter(this)" checked>
            oda astroquery-related nodes</label>
        </div>
        
        '''
    if graph_config_names_list is not None:
        html_code += ('<div style="margin: 15px 0px 10px 5px; font-weight: bold;">Enable/disable graphical configurations for the graph</div>')
        for graph_config_name in graph_config_names_list:
            html_code += f'''
                <div style="margin: 5px">
                    <label><input type="checkbox" id="config_{graph_config_name}" value="{graph_config_name}" onchange="toggle_graph_config(this)" checked>
                    {graph_config_name}</label>
                 </div>
            '''

    html_code += '''
            <div id="mynetwork"></div>
    '''

    net.html = net.html.replace('<div id = "mynetwork"></div>', html_code)
    with open(output_path, "w+") as out:
        out.write(net.html)


def add_js_click_functionality(net, output_path, graph_ttl_stream=None, graph_config_obj_dict=None):
    f_graph_vars = f'''
    
        // initialize global variables and graph configuration
        const graph_config_obj_default = {{ 
            "Default": {{
                "shape": "box",
                "color": "#FFFFFF",
                "style": "filled",
                "border": 0,
                "cellborder": 0,
                "value": 20,
                "config_file": null,
                "font": {{
                    "bold": {{
                        "size": 20
                    }}
                }}
           }}
        }}
        var graph_config_obj = JSON.parse('{graph_config_obj_dict}');
        
        const parser = new N3.Parser({{ format: 'ttl' }});
        let prefixes_graph = {{}};
        const store = new N3.Store();
        var options_repulsion, options_hierarchical;
        const myEngine = new Comunica.QueryEngine();
        const query_initial_graph = `CONSTRUCT {{
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
            }}`
    '''

    f_enable_filter = '''
        function enable_filter(check_box_element) {
            /* if(check_box_element.checked) {
                
            } */
        }
    '''

    f_apply_layout = '''
        function apply_layout(radio_box_element) {
            let layout_id = radio_box_element.id;
            let layout_name = layout_id.split("_")[0];
            switch (layout_name) {
                case "hierarchical":
                    network.setOptions( options_hierarchical );
                    break;
                
                case "repulsion": 
                    network.setOptions( options_repulsion );
                    break;
               
                default: 
                    network.setOptions( options );
            }
        }
    '''

    f_toggle_graph_config = '''
    
        function update_nodes(nodes_to_update, node_properties) {
            for (let i in nodes_to_update) {
                node_to_update_id = nodes_to_update[i]['id'];
                nodes.update({ 
                    id: node_to_update_id,
                    color: node_properties['color'],
                    border: node_properties['color'],
                    cellborder: node_properties['color'],
                    shape: node_properties['shape'],
                    style: node_properties['style'],
                    value: node_properties['value'],
                    config_file: node_properties['config_file'],
                });
            }
        }
    
        function toggle_graph_config(check_box_element) {
            let checked_config_id = check_box_element.id;
            if(check_box_element.checked) {
                let graph_config_obj_asArray = Object.entries(graph_config_obj);
                let config_subset =  graph_config_obj_asArray.filter(config => 'config_' + config[1].config_file === checked_config_id);
                for (let config_idx in config_subset) {
                    let node_properties = config_subset[config_idx][1];
                    let nodes_to_update = nodes.get({
                        filter: function (node) {
                            return (node.type_name === config_subset[config_idx][0]);
                        }
                    });
                    update_nodes(nodes_to_update, node_properties);
                }
            } else {
                let nodes_to_update = nodes.get({
                    filter: function (node) {
                        return ('config_' + node.config_file === checked_config_id);
                    }
                });
                update_nodes(nodes_to_update, graph_config_obj_default['Default']);
            }
        }
    '''

    f_reset_graph = '''
        function reset_graph() {
            nodes.clear();
            edges.clear();
            
            (async() => {
                const bindingsStreamCall = await myEngine.queryQuads(query_initial_graph,
                    {
                        sources: [ store ] 
                    }
                ); 
                bindingsStreamCall.on('data', (binding) => {
                    process_binding(binding);
                });
                bindingsStreamCall.on('end', () => {
                    let checked_radiobox = document.querySelector('input[name="graph_layout"]:checked');
                    apply_layout(checked_radiobox);
                });
                bindingsStreamCall.on('error', (error) => {
                    console.error(error);
                });
            })();
            
        }
    '''

    f_query_clicked_node_formatting = '''

            function format_query_clicked_node(clicked_node_id) {
            
                let filter_s = '';
                let filter_s_type = '';
                let filter_o = '';
                let filter_o_type = '';
                let filter_p = '';
                let filter_p_literal = '';
                for (let prefix_idx in prefixes_graph) {
                        let checkbox_config = document.getElementById(prefix_idx + '_filter');
                        if (checkbox_config !== null && !checkbox_config.checked) {
                            let values_input = checkbox_config.value.split(",");
                            for (let value_input_idx in values_input) {
                                filter_s += `FILTER ( ! STRSTARTS(STR(?s), "${prefixes_graph[values_input[value_input_idx].trim()]}") ). `;
                                filter_o += `FILTER ( ! STRSTARTS(STR(?o), "${prefixes_graph[values_input[value_input_idx].trim()]}") ). `;
                                filter_p += `FILTER ( ! STRSTARTS(STR(?p), "${prefixes_graph[values_input[value_input_idx].trim()]}") ). `;
                                filter_s_type += `FILTER ( ! STRSTARTS(STR(?s_type), "${prefixes_graph[values_input[value_input_idx].trim()]}") ). `;
                                filter_o_type += `FILTER ( ! STRSTARTS(STR(?o_type), "${prefixes_graph[values_input[value_input_idx].trim()]}") ). `;
                                filter_p_literal += `FILTER ( ! STRSTARTS(STR(?p_literal), "${prefixes_graph[values_input[value_input_idx].trim()]}") ). `;
                            }
                        }
                    }

                let query = `CONSTRUCT {
                    ?s ?p <${clicked_node_id}> ;
                        a ?s_type ;
                        ?p_literal ?s_literal .
                    
                    <` + clicked_node_id + `> ?p ?o .
                    ?o a ?o_type . 
                    ?o ?p_literal ?o_literal .
                }
                WHERE {
                    {
                        ?s ?p <${clicked_node_id}> .
                        ?s a ?s_type .
                        ?s ?p_literal ?s_literal .
                        FILTER isLiteral(?s_literal) .
                        ${filter_s_type}
                        ${filter_p_literal}
                    }
                    # UNION
                    # {
                    #     ?s ?p <${clicked_node_id}> .
                    #     ${filter_s}
                    # }
                    UNION
                    {
                        <${clicked_node_id}> ?p ?o .
                        ?o a ?o_type .
                        ?o ?p_literal ?o_literal .
                        FILTER isLiteral(?o_literal) .
                        ${filter_o_type}
                        ${filter_p_literal}
                    }
                    # UNION
                    # {
                    #     <${clicked_node_id}> ?p ?o .
                    #     ${filter_o}
                    # }
                }`;
                
                return query
            }
            '''

    f_process_binding = '''
        
        function process_binding(binding) {
            let subj_id = binding.subject.id ? binding.subject.id : binding.subject.value;
            let obj_id = binding.object.id ? binding.object.id : binding.object.value;
            let edge_id = subj_id + "_" + obj_id;
            
            subj_node = {
                id: subj_id,
                label: binding.subject.value ? binding.subject.value : binding.subject.id,
                title: subj_id,
                clickable: true,
                color: graph_config_obj_default['Default']['color'],
                shape: graph_config_obj_default['Default']['shape'],
                style: graph_config_obj_default['Default']['style'],
                border: graph_config_obj_default['Default']['border'],
                cellborder: graph_config_obj_default['Default']['cellborder'],
                value: graph_config_obj_default['Default']['value'],
                level: graph_config_obj_default['Default']['level'],
                config_file: graph_config_obj_default['Default']['config_file'],
                font: {
                      'multi': "html",
                      'face': "courier",
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
                title: obj_id,
                clickable: true,
                color: graph_config_obj_default['Default']['color'],
                shape: graph_config_obj_default['Default']['shape'],
                style: graph_config_obj_default['Default']['style'],
                border: graph_config_obj_default['Default']['border'],
                cellborder: graph_config_obj_default['Default']['cellborder'],
                value: graph_config_obj_default['Default']['value'],
                config_file: graph_config_obj_default['Default']['config_file'],
                font: {
                      'multi': "html",
                      'face': "courier",
                     }
            }
            if(!nodes.get(subj_id)) {
                nodes.add([subj_node]); 
            }
            if(binding.predicate.value.endsWith('#type')) {
                // extract type name
                idx_slash = obj_id.lastIndexOf("/");
                substr_q = obj_id.slice(idx_slash + 1); 
                if (substr_q) {
                    idx_hash = substr_q.indexOf("#");
                    if (idx_hash)
                      type_name = substr_q.slice(idx_hash + 1); 
                }
                subj_node_to_update = nodes.get(subj_id);
                // check type_name property of the node ahs already been defined previously
                if(!('type_name' in subj_node_to_update)) {
                
                    subj_node_to_update['label'] = '<b>' + type_name + '</b>\\n';
                    let node_properties =  { ... graph_config_obj_default['Default'], ... (graph_config_obj[type_name] ? graph_config_obj[type_name] : graph_config_obj_default['Default'])};
                    let config_value = node_properties['config_file'];
                    let checkbox_config = document.getElementById('config_' + config_value);
                    if(checkbox_config && !checkbox_config.checked)
                        node_properties = graph_config_obj_default['Default'];
                    nodes.update({ id: subj_id,
                                    label: subj_node_to_update['label'],
                                    type_name: type_name,
                                    color: node_properties['color'],
                                    border: node_properties['color'],
                                    cellborder: node_properties['color'],
                                    shape: node_properties['shape'],
                                    style: node_properties['style'],
                                    value: node_properties['value'],
                                    config_file: node_properties['config_file'],
                                    font: node_properties['font']
                                    });
                }
            }
            else {
                if(!edges.get(edge_id)) {
                    edges.add([edge_obj]);
                }
                if(!nodes.get(obj_id)) {
                    if(binding.object.termType === "Literal") {
                        subj_node_to_update = nodes.get(subj_id);
                        literal_predicate_index = edge_obj['title'].lastIndexOf("/")
                        literal_predicate = edge_obj['title'].slice(literal_predicate_index + 1);
                        if (literal_predicate) {
                            idx_hash = literal_predicate.indexOf("#");
                            if (idx_hash)
                              literal_predicate = literal_predicate.slice(idx_hash + 1); 
                        }
                        literal_label = literal_predicate + ': ' + obj_node['label'] + '\\n'
                        if(subj_node_to_update['label'].indexOf(literal_label) === -1)
                            nodes.update({
                                id: subj_id, 
                                label: subj_node_to_update['label'] + literal_label,
                                });
                    }
                }
            }
        }
          
        function drawGraph() {

    '''

    f_draw_graph = f'''
        parsed_graph = parser.parse(`{graph_ttl_stream}`,
            function (error, triple, prefixes) {{
                // Always log errors
                if (error) {{
                    console.error(error);
                }}
                if (triple) {{
                    store.addQuad(triple.subject, triple.predicate, triple.object);
                }} else {{
                    prefixes_graph = prefixes;
                }}
                
            }}
        );
        
        network.on("stabilized", function (e) {{
            network.setOptions( {{ "physics": {{ enabled: false }} }} );
        }});
        
        network.on("click", function(e) {{
            if(e.nodes[0]) {{
                selected_node = nodes.get(e.nodes[0]);
                if (selected_node && selected_node['clickable']) {{
                    network.setOptions( {{ "physics": {{ enabled: true }} }} );
                    // selected_node['expanded'] = true;
                    
                    myEngine.queryQuads(
                        format_query_clicked_node(selected_node.id),
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
                                network.setOptions( {{ "physics": {{ enabled: true }} }} );
                            }});
                            bindingsStream.on('error', (error) => {{
                                console.error("error when clicked a node: " + error);
                            }});
                        }}
                    );
                }}
                // TODO to be well defined the behavior  
                /* else if(selected_node && selected_node['clickable'] && selected_node['expanded'] ) {{
                    console.log("removal of the clicked node");
                    // do not really need to set to not-expanded since the node will be removed
                    selected_node['expanded'] = false;
                    nodes.remove(selected_node);
                }} */
            }}
        }});
        
        (async() => {{
            const bindingsStreamCall = await myEngine.queryQuads(query_initial_graph,
                {{
                    sources: [ store ] 
                }}
            ); 
            bindingsStreamCall.on('data', (binding) => {{
                process_binding(binding);
            }});
            bindingsStreamCall.on('end', () => {{
                network.setOptions( {{ "physics": {{ enabled: true }} }} );
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
        net.html = net.html.replace(net_html_match.group(0),
                                    f_enable_filter +
                                    f_apply_layout +
                                    f_toggle_graph_config +
                                    f_reset_graph +
                                    f_query_clicked_node_formatting +
                                    f_process_binding)

    net.html = net.html.replace('// initialize global variables.', f_graph_vars)

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
                                             src="https://rdf.js.org/comunica-browser/versions/latest"
                                                 "/engines/query-sparql-rdfjs/comunica-browser.js")
    soup.head.append(new_script_query_sparql_library)

    # save the file again
    with open(html_fn, "w") as outf:
        outf.write(str(soup))
