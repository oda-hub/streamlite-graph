import re
import typing
import pydotplus
import bs4

from lxml import etree
from dateutil import parser


def set_graph_options(net, output_path):
    options_str = (
        """
        
        var options = {
            autoResize: true,
            nodes: {
                scaling: {
                    min: 10,
                    max: 30
                },
                font: {
                    size: 14,
                    face: "Tahoma",
                },
            },
            edges: {
                smooth: {
                    type: "continuous"
                },
                arrows: {
                  to: {
                    enabled: true,
                    scaleFactor: 1.2
                    }
                },
                width: 4
                
            },
            layout: {
                hierarchical: {
                    enabled: false
                }
            },
            interaction: {
                
            },
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


def set_html_content(net, output_path, graph_config_names_list=None, graph_config_obj_dict=None, graph_reduction_config_dict=None):
    html_code = '''
        <div style="margin: 5px 0px 15px 5px">
            <button type="button" onclick="reset_graph()">Reset graph!</button>
            <button type="button" onclick="fit_graph()">Fit graph!</button>
            <button type="button" onclick="stop_animation()">Stop animation!</button>
        </div>
        <div style="display:flex;">
            <div style="background-color: #F7F7F7; border-left: 1px double; border-right: 1px double; padding: 5px; margin: 5px 0px 10px 5px">
                <h3 style="margin: 15px 0px 10px 5px;">Change graph layout</h3>
                
                <div style="margin: 5px">
                    <label><input type="radio" id="repulsion_layout" name="graph_layout" value="repulsion" onchange="apply_layout(this)" checked>
                    Random</label>
                </div>
                <div style="margin: 5px">
                    <label><input type="radio" id="hierarchical_layout" name="graph_layout" value="hierarchicalRepulsion" onchange="apply_layout(this)" unchecked>
                    Hierarchical</label>
                </div>
            </div>
            
            <div style="background-color: #F7F7F7; border-right: 1px double; padding: 5px; margin: 5px 0px 10px 5px">
                <h3 style="margin: 15px 0px 10px 5px;">Enable/disable selections for the graph</h3>
                
                <div style="margin: 5px">
                    <label><input type="checkbox" id="oda_filter" value="oda, odas" onchange="enable_filter(this)" checked>
                    oda astroquery-related nodes</label>
                </div>
            </div>
        '''
    if graph_reduction_config_dict is not None:
        html_code += ('<div style="background-color: #F7F7F7; border-right: 1px double; padding: 5px; margin: 5px 0px 10px 5px">'
                      '<h3 style="margin: 15px 0px 10px 5px;">Apply reductions on the graph</h3>')
        for reduction_obj_id in graph_reduction_config_dict:
            html_code += (f'''
                <div style="margin: 5px">
                    <label><input type="checkbox" id="reduction_config_{reduction_obj_id}" onchange="apply_reduction_change(this)"
                    value="{reduction_obj_id}" unchecked>{graph_reduction_config_dict[reduction_obj_id]["name"]}</label>
                </div>
            ''')
        html_code += '</div>'

    checkboxes_config_added = []
    if graph_config_names_list is not None:
        html_code += ('<div style="border-right: 1px double; padding: 5px; background-color: #F7F7F7; margin: 5px 0px 15px 5px">'
                      '<h3 style="margin: 15px 0px 10px 5px;">Enable/disable graphical configurations for the graph</h3>')
        for config_node_type in graph_config_obj_dict:
            if 'config_file' in graph_config_obj_dict[config_node_type]:
                graph_config_name = graph_config_obj_dict[config_node_type]['config_file']
                if graph_config_name not in checkboxes_config_added:
                    # for graph_config_name in graph_config_names_list:
                    html_code += f'''
                        <div style="margin: 5px">
                            <label><input type="checkbox" id="config_{graph_config_name}" value="{graph_config_name}" onchange="toggle_graph_config(this)" checked>
                            {graph_config_name}</label>
                        </div>
                    '''
                    checkboxes_config_added.append(graph_config_name)
    html_code += '''
                </div>
            </div>
            <div style="display: flex;">
                <div style="margin:10px;">
                    <div style="margin: 0px 0px 5px 5px; font-weight: bold; ">Legend</div>
                    <ul id="legend_container" style="overflow: scroll; padding-right:15px; overflow-x:hidden; background-color: #F7F7F7"></ul>
                </div>
                <div id="mynetwork"></div>
            </div>
    '''

    net.html = net.html.replace('<div id = "mynetwork"></div>', html_code)
    with open(output_path, "w+") as out:
        out.write(net.html)


def add_js_click_functionality(net, output_path, graph_ttl_stream=None, graph_config_obj_dict=None, graph_reductions_obj_dict=None):
    f_graph_vars = f'''
    
        // initialize global variables and graph configuration
        const graph_config_obj_default = {{ 
            "default": {{
                "shape": "box",
                "color": "#FFFFFF",
                "style": "filled",
                "border": 0,
                "cellborder": 0,
                "value": 20,
                "config_file": null,
                "font": {{
                    "multi": "html",
                    "face": "courier",
                    "size": 24,
                    "bold": {{
                        "size": 36
                    }}
                }},
                "margin": 10
           }}
        }}
        var graph_reductions_obj = JSON.parse('{graph_reductions_obj_dict}');
        var graph_config_obj = JSON.parse('{graph_config_obj_dict}');
        
        const parser = new N3.Parser({{ format: 'ttl' }});
        let prefixes_graph = {{}};
        const stack_promises = [];
        const store = new N3.Store();
        const myEngine = new Comunica.QueryEngine();
        const query_initial_graph = `CONSTRUCT {{
            ?action a <http://schema.org/Action> ;
                <https://swissdatasciencecenter.github.io/renku-ontology#command> ?actionCommand .
    
            ?activity a ?activityType ;
                <http://www.w3.org/ns/prov#startedAtTime> ?activityTime ;
                <http://www.w3.org/ns/prov#hadPlan> ?action .
            }}
            WHERE {{ 
                ?action a <http://schema.org/Action> ;
                    <https://swissdatasciencecenter.github.io/renku-ontology#command> ?actionCommand .
                     
                ?activity a ?activityType ;
                    <http://www.w3.org/ns/prov#startedAtTime> ?activityTime ;
                    <http://www.w3.org/ns/prov#qualifiedAssociation>/<http://www.w3.org/ns/prov#hadPlan> ?action .
            }}`
    '''

    f_enable_filter = '''
        function enable_filter(check_box_element) {
            /* if(check_box_element.checked) {
                
            } */
        }
    '''

    f_apply_reduction_change = '''
        function apply_reduction_change(check_box_element) {
            let checked_reduction_id = check_box_element.id.replace("reduction_config_", "");
            if (checked_reduction_id in graph_reductions_obj) {
                let reduction_subset =  graph_reductions_obj[checked_reduction_id];
                let predicates_to_absorb_list = reduction_subset["predicates_to_absorb"].split(",");
                let origin_node_list = nodes.get({
                    filter: function (item) {
                        return (item.hasOwnProperty("type_name") && item.type_name == checked_reduction_id);
                    }
                });
                if(check_box_element.checked) {
                    for (i in origin_node_list) {
                        let origin_node = origin_node_list[i];
                        let connected_edges = network.getConnectedEdges(origin_node.id);
                        let new_label = origin_node.label;
                        let longest_line = -1;
                        let original_label = origin_node.label;
                        let child_nodes_list_content = []
                        for (j in connected_edges) {
                            let connected_edge = edges.get(connected_edges[j]);
                            if (predicates_to_absorb_list.indexOf(connected_edge.title) > -1) {
                                let edge_nodes = network.getConnectedNodes(connected_edges[j]);
                                edges.remove(connected_edges[j]);
                                let node_removed = nodes.get(edge_nodes[1]);
                                if (edge_nodes[0] == origin_node.id) {
                                    nodes.remove(edge_nodes[1]);
                                }
                                else {
                                    node_removed = nodes.get(edge_nodes[0]);
                                    nodes.remove(edge_nodes[0]);
                                }
                                if (origin_node.hasOwnProperty('child_nodes_list_content'))
                                    child_nodes_list_content = origin_node.child_nodes_list_content; 
                                child_nodes_list_content.push([JSON.stringify(node_removed), JSON.stringify(connected_edge)]);
                                
                                let label_to_add = '\\n' + node_removed.displayed_type_name + ': ' + 
                                    node_removed.label.replaceAll('\\n', '')
                                                      .replaceAll(node_removed.displayed_type_name, '');
                                new_label += label_to_add;
                                origin_node = nodes.get(origin_node.id);
                            }
                        }
                        nodes.update({ 
                            id: origin_node.id,
                            label: new_label,
                            original_label: original_label,
                            child_nodes_list_content: child_nodes_list_content
                        });
                    }
                } else {
                    for (i in origin_node_list) {
                        // fix all the current nodes
                        fix_release_nodes();
                        let origin_node = origin_node_list[i];
                        if (origin_node.hasOwnProperty('child_nodes_list_content') && 
                            origin_node.child_nodes_list_content.length > 0) {
                            draw_child_nodes(origin_node);
                        }
                    }
                }
            }
        }
    '''

    f_generate_child_nodes = '''
        function draw_child_nodes(origin_node) {
            let position_origin_node = network.getPosition(origin_node.id);
            for (j in origin_node.child_nodes_list_content) {
                let child_node_obj = JSON.parse(origin_node.child_nodes_list_content[j][0]);
                let edge_obj = JSON.parse(origin_node.child_nodes_list_content[j][1]);
                child_node_obj['x'] = position_origin_node.x;
                child_node_obj['y'] = position_origin_node.y; 
                nodes.add([child_node_obj]);
                edges.add([edge_obj]);
            }
            nodes.update({ 
                id: origin_node.id,
                label: origin_node.original_label,
                child_nodes_list_content: []
            });
            let checked_radiobox = document.querySelector('input[name="graph_layout"]:checked');
            apply_layout(checked_radiobox);
        }
    '''

    f_apply_layout = '''
        function apply_layout(radio_box_element) {
            let layout_id = radio_box_element.id;
            let layout_name = layout_id.split("_")[0];
            switch (layout_name) {
                case "hierarchical":
                    network.setOptions(
                        {
                            "layout": {
                                "hierarchical": {
                                    enabled: true,
                                    levelSeparation: 300,
                                    sortMethod: "directed",
                                    nodeSpacing: 150
                                }
                            },
                            "physics": {
                                enabled: true,
                                minVelocity: 1,
                                maxVelocity: 100,
                                solver: "hierarchicalRepulsion",
                                hierarchicalRepulsion: {
                                    nodeDistance: 250,
                                },
                                stabilization: {
                                    enabled: true,
                                    updateInterval: 25,
                                    iterations: 1000
                                },
                            }
                        }
                    );
                    break;
                
                case "repulsion": 
                    network.setOptions(
                        {
                            "layout": {
                                "hierarchical": {
                                    "enabled": false
                                }
                            },
                            "physics": {
                                enabled: true,
                                minVelocity: 0.75,
                                 timestep: 0.35,
                                maxVelocity: 100,
                                solver: "repulsion",
                                forceAtlas2Based: {
                                    gravitationalConstant: -3500,
                                    centralGravity: 0.09,
                                    springLength: 300,
                                    springConstant: 1
                                },
                                repulsion: {
                                    nodeDistance: 350,
                                    centralGravity: 1.05,
                                    springConstant: 0.05,
                                    springLength: 250
                                },
                                stabilization: {
                                    enabled: true,
                                    updateInterval: 25,
                                    iterations: 1000
                                },
                            }
                        }
                    );
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
        
        function reset_legend() {
            let span_config_list = document.querySelectorAll('[id^="span_"]');
            for (i = 0; i < span_config_list.length; i++) {
                span_config_list[i].remove();
            }
            
            let legend_container = document.getElementById('legend_container');
            for (let config in graph_config_obj) {
                let check_box_config = document.getElementById('config_' + graph_config_obj[config]['config_file']);
                if(check_box_config && check_box_config.checked) {
                
                    let outer_li = document.createElement("li");
                    outer_li.setAttribute("id", `span_${config}`);
                    outer_li.setAttribute("style", "position: relative; margin: 5px; font-size: small;");
                    
                    let color_span = document.createElement("span");
                    let color = graph_config_obj[config]['color'];
                    color_span.setAttribute("style", `border-style: solid; border-width: 1px; width: 14px; height: 14px; display: inline-block; position: absolute; background-color: ${color};`);
                    
                    let name_span = document.createElement("span");
                    name_span.setAttribute("style", "margin-left: 20px;");
                    name_span.innerText = config;
                    
                    outer_li.appendChild(color_span);
                    outer_li.appendChild(name_span);
                    
                    legend_container.append(outer_li);
                }
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
                update_nodes(nodes_to_update, graph_config_obj_default['default']);
            }
            reset_legend();
        }
    '''

    f_fit_graph = '''
        function fit_graph() {
            network.fit();
        }
    '''

    f_extract_type_string = '''
        function extract_type_string(string_to_parse) {
            idx_slash = string_to_parse.lastIndexOf("/");
            substr_q = string_to_parse.slice(idx_slash + 1); 
            if (substr_q) {
                idx_hash = substr_q.indexOf("#");
                if (idx_hash)
                    return type = substr_q.slice(idx_hash + 1); 
            }
        }
    '''

    f_stop_animation = '''
        function stop_animation() {
            // fix_release_nodes(false);
            network.setOptions( { "physics": { enabled: false } } );
        }
    '''

    f_reset_graph = '''
        function reset_graph() {
            // retrieve all nodes that are not part of the legend
            let nodes_to_remove = nodes.get({
              filter: function (item) {
                return (!item.hasOwnProperty("group" ) || ! (item.group.startsWith("legend_")));
              }
            });
        
            nodes.remove(nodes_to_remove);
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

    f_query_node_type = '''
        function query_type_node(node_id) {
            let type;
            let query = `SELECT ?type WHERE { <${node_id}> a ?type }`;
            return myEngine.queryBindings(
                query,
                {
                    sources: [ store ]
                }
            );
        }
    '''

    f_query_clicked_node_formatting = '''

            function format_query_clicked_node(clicked_node_id) {
            
                let filter_s_type = '';
                let filter_s = '';
                let filter_o_type = '';
                let filter_o = '';
                let filter_p_literal = '';
                for (let prefix_idx in prefixes_graph) {
                        let checkbox_config = document.getElementById(prefix_idx + '_filter');
                        if (checkbox_config !== null && !checkbox_config.checked) {
                            let values_input = checkbox_config.value.split(",");
                            for (let value_input_idx in values_input) {
                                filter_s_type += `FILTER ( ! STRSTARTS(STR(?s_type), "${prefixes_graph[values_input[value_input_idx].trim()]}") ). `;
                                filter_s += `FILTER ( ! STRSTARTS(STR(?s), "${prefixes_graph[values_input[value_input_idx].trim()]}") ). `;
                                filter_o_type += `FILTER ( ! STRSTARTS(STR(?o_type), "${prefixes_graph[values_input[value_input_idx].trim()]}") ). `;
                                filter_o += `FILTER ( ! STRSTARTS(STR(?o), "${prefixes_graph[values_input[value_input_idx].trim()]}") ). `;
                                filter_p_literal += `FILTER ( ! STRSTARTS(STR(?p_literal), "${prefixes_graph[values_input[value_input_idx].trim()]}") ). `;
                            }
                        }
                    }

                let query = `CONSTRUCT {
                    ?s ?p <${clicked_node_id}> ;
                        a ?s_type ;
                        ?p_literal ?s_literal .
                    
                    <${clicked_node_id}> ?p ?o .
                    ?o a ?o_type . 
                    ?o ?p_literal ?o_literal .
                
                    ?action a <http://schema.org/Action> ;
                        <https://swissdatasciencecenter.github.io/renku-ontology#command> ?actionCommand .
            
                    ?activity a ?activityType ;
                        <http://www.w3.org/ns/prov#startedAtTime> ?activityTime ;
                        <http://www.w3.org/ns/prov#hadPlan> ?action .
                }
                WHERE {
                    {
                        ?s ?p <${clicked_node_id}> .
                        ?s a ?s_type .
                        ?s ?p_literal ?s_literal .
                        FILTER isLiteral(?s_literal) .
                        ${filter_s_type}
                        ${filter_p_literal}
                        
                        FILTER (?p != <http://www.w3.org/ns/prov#qualifiedAssociation> && 
                                ?p != <http://www.w3.org/ns/prov#hadPlan> ) .
                    }
                    UNION
                    {
                        ?s ?p <${clicked_node_id}> .
                        ?s a ?s_type .
                        ${filter_s_type}
                        
                        FILTER (?p != <http://www.w3.org/ns/prov#qualifiedAssociation> && 
                                ?p != <http://www.w3.org/ns/prov#hadPlan> ) .
                    }
                    UNION
                    {
                        ?s ?p <${clicked_node_id}> .
                        ${filter_s}
                        
                        FILTER (?p != <http://www.w3.org/ns/prov#qualifiedAssociation> && 
                                ?p != <http://www.w3.org/ns/prov#hadPlan> ) .
                    }
                    UNION
                    {
                        <${clicked_node_id}> ?p ?o .
                        ?o a ?o_type .
                        ?o ?p_literal ?o_literal .
                        FILTER isLiteral(?o_literal) .
                        ${filter_o_type}
                        ${filter_p_literal}
                    
                        FILTER (?p != <http://www.w3.org/ns/prov#qualifiedAssociation> && 
                                ?p != <http://www.w3.org/ns/prov#hadPlan> ) .                    
                    }
                    UNION
                    {
                        <${clicked_node_id}> ?p ?o .
                        ?o a ?o_type
                        ${filter_o_type}

                        FILTER (?p != <http://www.w3.org/ns/prov#qualifiedAssociation> && 
                                ?p != <http://www.w3.org/ns/prov#hadPlan> ) .
                    }
                    UNION
                    {
                        <${clicked_node_id}> ?p ?o .
                        ${filter_o}
                        
                        FILTER (?p != <http://www.w3.org/ns/prov#qualifiedAssociation> && 
                                ?p != <http://www.w3.org/ns/prov#hadPlan> ) .
                    }
                    UNION
                    {
                        ?action a <http://schema.org/Action> ;
                            <https://swissdatasciencecenter.github.io/renku-ontology#command> ?actionCommand .
                             
                        ?activity a ?activityType ;
                            <http://www.w3.org/ns/prov#startedAtTime> ?activityTime ;
                            <http://www.w3.org/ns/prov#qualifiedAssociation>/<http://www.w3.org/ns/prov#hadPlan> ?action .
                        
                        FILTER (?activity = <${clicked_node_id}> ||
                                ?action = <${clicked_node_id}> ) .
                        
                    }
                }`;
                
                return query
            }
            '''
    f_fix_release_nodes = '''
        function fix_release_nodes(fix) {
            if (fix === undefined)
                fix = true;
            nodes.forEach(node => {
                nodes.update({id: node.id, fixed: fix});
            });
        }
    '''
    f_process_binding = '''
        function process_binding(binding, clicked_node, list_node_ids_already_added, list_edge_ids_already_added, node_reduction_obj) {
            let checkbox_reduction;
            if (clicked_node !== undefined && clicked_node.hasOwnProperty("type_name"))
                checkbox_reduction = document.getElementById('reduction_config_' + clicked_node.type_name);
        
            let subj_id = binding.subject.id ? binding.subject.id : binding.subject.value;
            let obj_id = binding.object.id ? binding.object.id : binding.object.value;
            let edge_id = subj_id + "_" + obj_id;
            
            subj_node = {
                id: subj_id,
                label: binding.subject.value ? binding.subject.value : binding.subject.id,
                title: subj_id,
                clickable: true,
                color: graph_config_obj_default['default']['color'],
                shape: graph_config_obj_default['default']['shape'],
                style: graph_config_obj_default['default']['style'],
                border: graph_config_obj_default['default']['border'],
                cellborder: graph_config_obj_default['default']['cellborder'],
                value: graph_config_obj_default['default']['value'],
                level: graph_config_obj_default['default']['level'],
                config_file: graph_config_obj_default['default']['config_file'],
                margin: graph_config_obj_default['default']['margin'],
                font: {
                      'multi': "html",
                      'face': "courier",
                     }
            }
            edge_obj = {
                id: edge_id,
                from: subj_id,
                to: obj_id,
                title: binding.predicate.value,
                font: {
                      'multi': "html",
                      'face': "courier",
                      'size': 24
                     }
            }
            obj_node = {
                id: obj_id,
                label: binding.object.value ? binding.object.value : binding.object.id,
                title: obj_id,
                clickable: true,
                color: graph_config_obj_default['default']['color'],
                shape: graph_config_obj_default['default']['shape'],
                style: graph_config_obj_default['default']['style'],
                border: graph_config_obj_default['default']['border'],
                cellborder: graph_config_obj_default['default']['cellborder'],
                value: graph_config_obj_default['default']['value'],
                config_file: graph_config_obj_default['default']['config_file'],
                level: graph_config_obj_default['default']['level'],
                margin: graph_config_obj_default['default']['margin'],
                font: {
                      'multi': "html",
                      'face': "courier",
                     }
            }
            
            if (clicked_node !== undefined) {
                let position_clicked_node = network.getPosition(clicked_node.id);
                
                subj_node['x'] = position_clicked_node.x;
                subj_node['y'] = position_clicked_node.y;
                
                obj_node['x'] = position_clicked_node.x;
                obj_node['y'] = position_clicked_node.y;
            }
            let type_name;
            if(binding.predicate.value.endsWith('#type'))
                type_name = extract_type_string(obj_id);
            //
            let literal_predicate_index = edge_obj['title'].lastIndexOf("/");
            let literal_predicate = edge_obj['title'].slice(literal_predicate_index + 1);
            if (literal_predicate) {
                idx_hash = literal_predicate.indexOf("#");
                if (idx_hash)
                    literal_predicate = literal_predicate.slice(idx_hash + 1); 
            }
            
            let type_node_not_to_be_absorbed = node_reduction_obj !== undefined && type_name !== null && node_reduction_obj["nodes_to_absorb"].indexOf(type_name) < 0;
            let predicate_not_to_be_absorbed = node_reduction_obj !== undefined && literal_predicate !== null && node_reduction_obj["predicates_to_absorb"].indexOf(literal_predicate) < 0;
            
            if(!nodes.get(subj_id) &&
                (list_node_ids_already_added === undefined ||
                (list_node_ids_already_added.indexOf(subj_id) < 0 &&
                 (checkbox_reduction === null || 
                 (checkbox_reduction !== null && !checkbox_reduction.checked) ||
                 (checkbox_reduction !== null && checkbox_reduction.checked && predicate_not_to_be_absorbed && type_node_not_to_be_absorbed)
                )
                )))
                nodes.add([subj_node]);
            else {
                // add info in the node
                
            }
            
            if(binding.predicate.value.endsWith('#type')) {
                // extract type name
                type_name = extract_type_string(obj_id);
                let subj_node_to_update = nodes.get(subj_id);
                // check type_name property of the node ahs already been defined previously
                if(subj_node_to_update !== null && !('type_name' in subj_node_to_update)) {
                    let node_properties =  { ... graph_config_obj_default['default'], ... (graph_config_obj[type_name] ? graph_config_obj[type_name] : graph_config_obj_default['default'])};
                    // displayed_literals_format:defaultValue:yes/defaultValue:no
                    // displayed_information:title/literals/both
                    if('displayed_information' in node_properties) {
                        switch (node_properties['displayed_information']) {
                            case 'title': 
                            case 'both':
                                if('displayed_type_name' in node_properties)
                                    subj_node_to_update['label'] = `<b>${node_properties['displayed_type_name']}</b>\\n`;
                                else
                                    subj_node_to_update['label'] = `<b>${type_name}</b>\\n`;
                                break;
                            case 'literals':
                                subj_node_to_update['label'] = '';
                                break;
                        }
                        
                        if('displayed_type_name' in node_properties)
                            subj_node_to_update['title'] = node_properties['displayed_type_name'];
                        else
                            subj_node_to_update['title']= type_name;
                    } else {
                        if('displayed_type_name' in node_properties) {
                            subj_node_to_update['label'] = `<b>${node_properties['displayed_type_name']}</b>\\n`;
                            subj_node_to_update['title'] = node_properties['displayed_type_name'];
                        }
                        else {
                            subj_node_to_update['label'] = subj_node_to_update['title'] = `<b>${type_name}</b>\\n`;
                            subj_node_to_update['title']= type_name;
                        }
                    }
                    let config_value = node_properties['config_file'];
                    let checkbox_config = document.getElementById('config_' + config_value);
                    if(checkbox_config && !checkbox_config.checked)
                        node_properties = graph_config_obj_default['default'];
                    nodes.update({ id: subj_id,
                                    label: subj_node_to_update['label'],
                                    title: subj_node_to_update['title'],
                                    type_name: type_name,
                                    displayed_type_name: node_properties['displayed_type_name'] ? node_properties['displayed_type_name'] : type_name,
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
                if(literal_predicate)
                    edge_obj['title'] = literal_predicate;
                if(!edges.get(edge_id) &&
                    (list_edge_ids_already_added === undefined ||
                    list_edge_ids_already_added.indexOf(edge_id) < 0) && 
                    (node_reduction_obj === undefined || 
                    node_reduction_obj["predicates_to_absorb"].indexOf(literal_predicate) < 0 ||
                        (node_reduction_obj["predicates_to_absorb"].indexOf(literal_predicate) > -1 && 
                        checkbox_reduction !== undefined && !checkbox_reduction.checked))) {
                    edge_obj['label'] = literal_predicate;
                    edges.add([edge_obj]);
                }
                if(!nodes.get(obj_id)) {
                    if(binding.object.termType === "Literal") {
                        subj_node_to_update = nodes.get(subj_id);
                        if(subj_node_to_update !== null) {
                            literal_predicate_index = edge_obj['title'].lastIndexOf("/");
                            literal_predicate = edge_obj['title'].slice(literal_predicate_index + 1);
                            if (literal_predicate) {
                                idx_hash = literal_predicate.indexOf("#");
                                if (idx_hash)
                                  literal_predicate = literal_predicate.slice(idx_hash + 1); 
                            }
                            
                            let literal_label = '';
                            
                            if(subj_node_to_update !== null && 'type_name' in subj_node_to_update) {
                                let type_name = subj_node_to_update['type_name']
                                let node_properties =  { ... graph_config_obj_default['default'], ... (graph_config_obj[type_name] ? graph_config_obj[type_name] : graph_config_obj_default['default'])};
                                // displayed_literals_format:defaultValue:yes / defaultValue:no
                                // displayed_information:title / literals / both
                                if('literals_keyword_to_substitute' in node_properties) {
                                    let literals_keyword_to_substitute = node_properties['literals_keyword_to_substitute'].split(";");
                                    for(let i in literals_keyword_to_substitute) {
                                        let literal_for_substitution = literals_keyword_to_substitute[i].split(":");
                                        if (literal_for_substitution[0] === literal_predicate) {
                                            let keywords_substitution_list = literal_for_substitution[1].split(",");
                                            for(let j in keywords_substitution_list) {
                                                let keyword = keywords_substitution_list[j];
                                                if (obj_node['label'].indexOf(keyword) > -1) {
                                                    obj_node['label'] = keyword;
                                                    break;
                                                }
                                            }
                                        }
                                    }
                                }
                                
                                if('displayed_information' in node_properties && node_properties['displayed_information'] !== "title" && 
                                    'displayed_literals_format' in node_properties) {
                                    if(node_properties['displayed_literals_format'].indexOf(`${literal_predicate}:`) > -1) {
                                        let literals_display_config = node_properties['displayed_literals_format'].split(",");
                                        for(let i in literals_display_config) {
                                            let literal_config = literals_display_config[i].split(":");
                                            if(literal_config[0] === literal_predicate) {
                                                switch(literal_config[1]) {
                                                    case "yes":
                                                        literal_label = literal_predicate + ': ' + obj_node['label'];
                                                        break;
                                                    case "no":
                                                        literal_label = obj_node['label'];
                                                        break;
                                                    default:
                                                        literal_label = literal_predicate + ': ' + obj_node['label'];
                                                        break;
                                                }
                                            }
                                        }
                                    }
                                } else if(! ('displayed_information' in node_properties)) {
                                    literal_label = literal_predicate + ': ' + obj_node['label'];
                                }
                            } else {
                                literal_label = literal_predicate + ': ' + obj_node['label'];
                            }
                            if(literal_label !== '' && subj_node_to_update['label'].indexOf(literal_label) === -1) {
                                if (subj_node_to_update['label']) {
                                    literal_label = "\\n" + literal_label;
                                }
                                nodes.update({
                                    id: subj_id, 
                                    label:  subj_node_to_update['label'] + literal_label,
                                });
                            }
                        }
                    }
                    else
                         if ((list_node_ids_already_added === undefined ||
                                (list_node_ids_already_added.indexOf(obj_id) < 0 &&
                                (checkbox_reduction === null || 
                                 (checkbox_reduction !== null && !checkbox_reduction.checked) ||
                                 (checkbox_reduction !== null && checkbox_reduction.checked && predicate_not_to_be_absorbed && type_node_not_to_be_absorbed)
                                )))
                            )
                            nodes.add([obj_node]);
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
            stop_animation();
        }});
        
        network.on("dragStart", function (e) {{
            stop_animation();    
            fix_release_nodes(false);    
        }});
        
        network.on("click", function(e) {{
            if(e.nodes[0]) {{
                if(nodes.get(e.nodes[0])['clickable']) {{
                    let clicked_node = nodes.get(e.nodes[0]);
                    if (!('expanded' in clicked_node) || !clicked_node['expanded']) {{
                        clicked_node['expanded'] = true;
                        // fix all the current nodes
                        fix_release_nodes();
                        // get list of node and edge ids not to be added
                        let list_node_ids_already_added = [];
                        let list_edge_ids_already_added = [];
                        if (clicked_node.hasOwnProperty('child_nodes_list_content') && 
                            clicked_node.child_nodes_list_content.length > 0) {{
                            for (j in clicked_node.child_nodes_list_content) {{
                                let child_node_obj = JSON.parse(clicked_node.child_nodes_list_content[j][0]);
                                let edge_obj =  JSON.parse(clicked_node.child_nodes_list_content[j][1]);
                                list_node_ids_already_added.push(child_node_obj.id);
                                list_edge_ids_already_added.push(edge_obj.id);
                            }}
                        }}
                        // get checked reductions checkboxes
                        let node_reduction_obj = graph_reductions_obj[clicked_node.type_name];
                        (async() => {{
                            const bindingsStreamCall = await myEngine.queryQuads(
                                format_query_clicked_node(clicked_node.id),
                                {{
                                    sources: [ store ]
                                }}
                            );
                            bindingsStreamCall.on('data', (binding) => {{
                                process_binding(binding, clicked_node, list_node_ids_already_added, list_edge_ids_already_added, node_reduction_obj);
                            }});
                            bindingsStreamCall.on('end', () => {{
                                let checked_radiobox = document.querySelector('input[name="graph_layout"]:checked');
                                apply_layout(checked_radiobox);
                            }});
                            bindingsStreamCall.on('error', (error) => {{ 
                                console.error(error);
                            }});
                        }})();
                    }}
                    else {{
                        let connected_to_nodes = network.getConnectedNodes(clicked_node.id);
                        let nodes_to_remove = [];
                        let edges_to_remove = [];
                        if (connected_to_nodes.length > 0) {{
                            for (let i in connected_to_nodes) {{
                                let connected_to_node = connected_to_nodes[i];
                                connected_to_connected_to_node = network.getConnectedNodes(connected_to_node);
                                if (connected_to_connected_to_node.length == 1) {{
                                    nodes_to_remove.push(connected_to_node);
                                    edges_to_remove.push(...network.getConnectedEdges(connected_to_node));
                                }}
                            }}
                        }}
                        
                        edges.remove(edges_to_remove);
                        nodes.remove(nodes_to_remove);
                        
                        clicked_node['expanded'] = false;
                    }}
                }}
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
                let checked_radiobox = document.querySelector('input[name="graph_layout"]:checked');
                apply_layout(checked_radiobox);
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
        
        // legend
        reset_legend();
        
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
                                    f_stop_animation +
                                    f_fit_graph +
                                    f_apply_reduction_change +
                                    f_generate_child_nodes +
                                    f_reset_graph +
                                    f_extract_type_string +
                                    f_query_node_type +
                                    f_query_clicked_node_formatting +
                                    f_fix_release_nodes +
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
