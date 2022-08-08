import json
import os
import sys

from pyvis.network import Network

import graph_utils as graph_utils
import streamlit as st
import streamlit.components.v1 as components

__this_dir__ = os.path.join(os.path.abspath(os.path.dirname(__file__)))

# -- Set page config
apptitle = 'Graph Quickview'

st.set_page_config(page_title=apptitle, page_icon=":eyeglasses:", layout="wide")
st.title('Graph Quick-Look')


def stream_graph():

    graph_config_fn_list = ['graph_data/graph_config.json', 'graph_data/graph_config_1.json']

    graph_exports_dict = {
        # 'oda-sdss': '',
        'renku-aqs-test-case one execution': 'graph_data/graph.ttl',
        'renku-aqs-test-case two executions': 'graph_data/graph_two_commands.ttl',
    }

    html_fn = 'graph_data/graph.html'
    ttl_fn = 'graph_data/graph_two_commands.ttl'

    graph_nodes_subset_config_fn = 'graph_data/graph_nodes_subset_config.json'

    graph_reduction_config_fn = 'graph_data/graph_reduction_config.json'

    col1, col2, col3 = st.columns(3)
    with col1:
        graph_selected = st.selectbox('Which graph example would you like to explore?',
                                      graph_exports_dict.keys())

    net = Network(
        height='750px', width='100%',
    )

    # to tweak physics related options
    net.write_html(html_fn)

    graph_utils.set_graph_options(net, html_fn)

    graph_selected_fn = graph_exports_dict.get(graph_selected, ttl_fn)
    fd = open(graph_selected_fn, 'r')
    graph_ttl_str = fd.read()
    fd.close()
    nodes_graph_config_obj = {}
    edges_graph_config_obj = {}

    graph_config_names_list = []
    for graph_config_fn in graph_config_fn_list:
        with open(graph_config_fn) as graph_config_fn_f:
            graph_config_loaded = json.load(graph_config_fn_f)
            nodes_graph_config_obj_loaded = graph_config_loaded.get('Nodes', {})
            edges_graph_config_obj_loaded = graph_config_loaded.get('Edges', {})

        if nodes_graph_config_obj_loaded:
            for config_type in nodes_graph_config_obj_loaded:
                nodes_graph_config_obj_loaded[config_type]['config_file'] = graph_config_fn
            nodes_graph_config_obj.update(nodes_graph_config_obj_loaded)
        if edges_graph_config_obj_loaded:
            for config_type in edges_graph_config_obj_loaded:
                edges_graph_config_obj_loaded[config_type]['config_file'] = graph_config_fn
            edges_graph_config_obj.update(edges_graph_config_obj_loaded)
        graph_config_names_list.append(graph_config_fn)
    # for compatibility with Javascript
    nodes_graph_config_obj_str = json.dumps(nodes_graph_config_obj)
    edges_graph_config_obj_str = json.dumps(edges_graph_config_obj)

    with open(graph_reduction_config_fn) as graph_reduction_config_fn_f:
        graph_reduction_config_obj = json.load(graph_reduction_config_fn_f)

    # for compatibility with Javascript
    graph_reductions_obj_str = json.dumps(graph_reduction_config_obj)

    with open(graph_nodes_subset_config_fn) as graph_nodes_subset_config_fn_f:
        graph_nodes_subset_config_obj = json.load(graph_nodes_subset_config_fn_f)

    # for compatibility with Javascript
    graph_nodes_subset_config_obj_str = json.dumps(graph_nodes_subset_config_obj)

    graph_utils.add_js_click_functionality(net, html_fn,
                                           graph_ttl_stream=graph_ttl_str,
                                           nodes_graph_config_obj_str=nodes_graph_config_obj_str,
                                           edges_graph_config_obj_str=edges_graph_config_obj_str,
                                           graph_reductions_obj_str=graph_reductions_obj_str,
                                           graph_nodes_subset_config_obj_str=graph_nodes_subset_config_obj_str)

    graph_utils.set_html_content(net, html_fn,
                                 graph_config_names_list=graph_config_names_list,
                                 nodes_graph_config_obj_dict=nodes_graph_config_obj,
                                 edges_graph_config_obj_dict=edges_graph_config_obj,
                                 graph_reduction_config_obj_dict=graph_reduction_config_obj,
                                 graph_nodes_subset_config_obj_dict=graph_nodes_subset_config_obj)

    graph_utils.update_js_libraries(html_fn)

    # webbrowser.open('graph_data/graph.html')
    st.components.v1.html(open(html_fn).read(), width=1700, height=1000, scrolling=True)

    st.markdown("***")


if __name__ == '__main__':
    stream_graph()
