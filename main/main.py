import pydotplus
import os
import yaml
import threading

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
    # dot_fn = 'graph_data/graph_base.dot'
    dot_fn = 'graph_data/graph.dot'
    html_fn = 'graph_data/graph.html'
    ttl_fn = 'graph_data/graph.ttl'

    # pydot_graph = pydotplus.graph_from_dot_file(dot_fn)
    net = Network(
        height='750px', width='100%',
    )

    # to tweak physics related options
    net.write_html(html_fn)

    graph_utils.set_graph_options(net, html_fn)

    fd = open(ttl_fn, 'r')
    graph_ttl_str = fd.read()
    fd.close()

    graph_utils.add_js_click_functionality(net, html_fn, graph_ttl_stream=graph_ttl_str)
    graph_utils.update_js_libraries(html_fn)

    # webbrowser.open('graph_data/graph.html')
    st.components.v1.html(open(html_fn).read(), width=1700, height=1000, scrolling=True)

    st.markdown("***")


if __name__ == '__main__':
    stream_graph()
