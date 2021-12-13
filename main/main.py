import pydotplus
import os
import yaml

from pyvis.network import Network
import graph_utils as graph_utils
import streamlit as st
import streamlit.components.v1 as components

__this_dir__ = os.path.join(os.path.abspath(os.path.dirname(__file__)))
graph_configuration = yaml.load(open(os.path.join(__this_dir__, "../graph_data/graph_config.yaml")), Loader=yaml.SafeLoader)
type_configuration = yaml.load(open(os.path.join(__this_dir__, "../graph_data/type_label_values_dict.yaml")), Loader=yaml.SafeLoader)

# -- Set page config
apptitle = 'Graph Quickview'

st.set_page_config(page_title=apptitle, page_icon=":eyeglasses:", layout="wide")
st.title('Graph Quick-Look')


def stream_graph():
    dot_fn = 'graph_data/graph.dot'
    html_fn = 'graph_data/graph.html'

    pydot_graph = pydotplus.graph_from_dot_file(dot_fn)
    net = Network(
        height='500px', width='100%',
    )

    net.set_options(
        """{
            "physics": {
                "barnesHut": {
                  "gravitationalConstant": -2850,
                  "centralGravity": 0.9,
                  "springConstant": 0,
                  "damping": 0.54
                },
                "minVelocity": 0.75
            }
        }"""
    )

    hidden_nodes_dic = {}
    hidden_edges = []

    for node in pydot_graph.get_nodes():
        id_node = graph_utils.get_id_node(node)
        if id_node is not None:
            type_node = type_configuration[id_node]
            node_configuration = graph_configuration.get(type_node,
                                                         graph_configuration['Default'])
            node_value = node_configuration.get('value', graph_configuration['Default']['value'])
            hidden = False
            if type_node.startswith('CommandOutput') or type_node.startswith('CommandInput'):
                hidden = True
            if not hidden:
                net.add_node(node.get_name(),
                             label=type_node,
                             color=node_configuration['color'],
                             shape=node_configuration['shape'],
                             value=node_value)
            else:
                node_info = dict(
                    id=node.get_name(),
                    label=type_node,
                    color=node_configuration['color'],
                    shape=node_configuration['shape'],
                    value=node_value
                )

                hidden_nodes_dic[node.get_name()] = node_info

    # list of edges and simple color change
    for edge in pydot_graph.get_edge_list():
        edge_label = graph_utils.get_edge_label(edge)
        source_node = edge.get_source()
        dest_node = edge.get_destination()
        hidden = False
        edge_id = (source_node + '_' + dest_node)
        if edge_label.startswith('isInputOf') or edge_label.startswith('hasOutputs'):
            hidden = True
        if source_node is not None and dest_node is not None:
            if not hidden:
                net.add_edge(source_node, dest_node,
                             id=edge_id,
                             title=edge_label)
            else:
                edge_info = dict(
                    source_node=source_node,
                    dest_node=dest_node,
                    id=edge_id,
                    title=edge_label
                )
                hidden_edges.append(edge_info)

    # to tweak physics related options
    # net.show_buttons(filter_=['physics'])
    net.write_html(html_fn)

    graph_utils.add_js_click_functionality(net, html_fn, hidden_nodes_dic, hidden_edges)

    # webbrowser.open('graph_data/graph.html')
    st.components.v1.html(open(html_fn).read(), width=1200, height=800, scrolling=True)
    st.markdown("***")


if __name__ == '__main__':
    stream_graph()

