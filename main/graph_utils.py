import typing
import pydotplus

from lxml import etree
from dateutil import parser


def get_node_label(node: typing.Union[pydotplus.Node],
                   type_node) -> str:
    node_label = ""
    if 'label' in node.obj_dict['attributes']:
        # parse the whole node table into a lxml object
        table_html = etree.fromstring(node.get_label()[1:-1])
        tr_list = table_html.findall('tr')
        for tr in tr_list:
            list_td = tr.findall('td')
            if len(list_td) == 2:
                list_left_column_element = list_td[0].text.split(':')
                if type_node == 'Action' and 'command' in list_left_column_element:
                    node_label = '' + list_td[1].text[1:-1] + '\n' + node_label
                if 'startedAtTime' in list_left_column_element:
                    parsed_startedAt_time = parser.parse(list_td[1].text.replace('^^xsd:dateTime', '')[1:-1])
                    # create an additional row to attach at the bottom, so that time is always at the bottom
                    node_label += parsed_startedAt_time.strftime('%Y-%m-%d %H:%M:%S') + '\n'
    if node_label == "":
        node_label = type_node
    return node_label


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
        console.log(selected_node);
        if (selected_node.type == "Action") {
        '''
    for hidden_edge in hidden_edges_dic:
        hidden_node_id = None
        if hidden_edge['dest_node'] in hidden_nodes_dic:
            hidden_node_id = hidden_edge['dest_node']
        elif hidden_edge['source_node'] in hidden_nodes_dic:
            hidden_node_id = hidden_edge['source_node']
        if hidden_node_id is not None:
            f_click += f'''
                if(selected_node.id == "{hidden_edge['source_node']}" || selected_node.id == "{hidden_edge['dest_node']}") {{
                    if(edges.get("{hidden_edge['id']}") == null) {{
                        nodes.add([
                            {{id: "{hidden_node_id}", 
                            shape: "{hidden_nodes_dic[hidden_node_id]['shape']}", 
                            color: "{hidden_nodes_dic[hidden_node_id]['color']}", 
                            label: "{hidden_nodes_dic[hidden_node_id]['label']}",
                            level: "{hidden_nodes_dic[hidden_node_id]['level']}",
                            value: "{hidden_nodes_dic[hidden_node_id]['value']}",
                            font: "{hidden_nodes_dic[hidden_node_id]['font']}"}}
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
        network.fit();
        network.redraw();
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
