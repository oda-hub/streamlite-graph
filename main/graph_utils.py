import typing
import pydotplus
from lxml import etree


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


def add_js_click_functionality(net, output_path):
    f_click = '''
    var toggle = false;
    network.on("click", function(e) {
    
        selected_node = nodes.get(e.nodes[0]);
        if (selected_node.label == "Action") {
            for (let i = 0; i < e.edges.length; i++) {
              let edge = edges.get(e.edges[i]);
              if (edge.title == "isInputOf" || edge.title == "hasOutputs") {
                  edges.update([
                    {id: edge.id, hidden: toggle}
                  ]);
                  let to_node = edges.get(e.edges[i]).to;
                  if (to_node != e.nodes[0]) {
                    nodes.update([
                        {id: to_node, hidden: toggle}
                    ]);
                  }
                  let from_node = edges.get(e.edges[i]).from;
                  if (from_node != e.nodes[0]) {
                    nodes.update([
                        {id: from_node, hidden: toggle}
                    ]);
                  }
              }
            }
            // switch toggle
            // network.fit();
            toggle = !toggle;
        }
    });
    return network;
    '''
    net.html = net.html.replace('return network;', f_click)

    with open(output_path, "w+") as out:
        out.write(net.html)
