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


def add_js_click_functionality(net, output_path, hidden_nodes_dic, hidden_edges_dic):
    f_click = '''
    var toggle = false;
    network.on("click", function(e) {
        selected_node = nodes.get(e.nodes[0]);
        if (selected_node.hasOwnProperty('type') && (selected_node.type == "Action" || selected_node.type.startsWith("Astrophysical"))) {
        '''
    for hidden_edge in hidden_edges_dic:
        hidden_node_id = None
        if hidden_edge['dest_node'] in hidden_nodes_dic:
            hidden_node_id = hidden_edge['dest_node']
        elif hidden_edge['source_node'] in hidden_nodes_dic:
            hidden_node_id = hidden_edge['source_node']
        if hidden_node_id is not None:
            node_label = hidden_nodes_dic[hidden_node_id]['label'].replace("\n", '\\n')
            node_title = hidden_nodes_dic[hidden_node_id]['title'].replace("\n", '\\n')
            f_click += f'''
                if(selected_node.id == "{hidden_edge['source_node']}" || selected_node.id == "{hidden_edge['dest_node']}") {{
                    if(edges.get("{hidden_edge['id']}") == null) {{
                        nodes.add([
                            {{id: "{hidden_node_id}",
                            label: "{node_label}",
                            title: "{node_title}",
                            color: "{hidden_nodes_dic[hidden_node_id]['color']}",
                            shape: "{hidden_nodes_dic[hidden_node_id]['shape']}",
                            type: "{hidden_nodes_dic[hidden_node_id]['type']}",
                            font: {hidden_nodes_dic[hidden_node_id]['font']},
                            level: "{hidden_nodes_dic[hidden_node_id]['level']}"}}
                        ]);
                        edges.add([
                            {{id: "{hidden_edge['id']}", 
                            from: "{hidden_edge['source_node']}", 
                            to: "{hidden_edge['dest_node']}", 
                            title:"{hidden_edge['title']}", 
                            hidden:false }}
                        ]);
                    }}
                    else {{
                        nodes.remove([
                            {{id: "{hidden_node_id}"}}
                        ])
                        edges.remove([
                            {{id: "{hidden_edge['id']}"}},
                        ]);
                    }}
                }}
        '''

    f_click += '''
        }
        // network.fit();
        // network.redraw();
    });
    
    var container_configure = document.getElementsByClassName("vis-configuration-wrapper");
    if(container_configure) {
        container_configure = container_configure[0];
        container_configure.style = {};
        container_configure.style.height="300px";
        container_configure.style.overflow="scroll";
    }
    return network;
    '''
    # container_configure.style.overflow-x = "hidden";
    # container_configure.style.overflow-y = "auto";
    # container_configure.style.height: 150px;
    # console.log(container_configure.style);
    net.html = net.html.replace('return network;', f_click)

    with open(output_path, "w+") as out:
        out.write(net.html)


def update_vis_library_version(html_fn):
    # let's patch the template
    # load the file
    with open(html_fn) as template:
        html_code = template.read()
        soup = bs4.BeautifulSoup(html_code, "html.parser")

    soup.head.link.decompose()
    soup.head.script.decompose()

    new_script = soup.new_tag("script", type="application/javascript",
                              src="https://unpkg.com/vis-network/standalone/umd/vis-network.js")
    soup.head.append(new_script)

    # save the file again
    with open(html_fn, "w") as outf:
        outf.write(str(soup))