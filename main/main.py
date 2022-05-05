import json
import os

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
    html_fn = 'graph_data/graph.html'
    ttl_fn = 'graph_data/graph.ttl'
    graph_config_fn = 'graph_data/graph_config.json'

    net = Network(
        height='750px', width='100%',
    )

    # to tweak physics related options
    net.write_html(html_fn)

    graph_utils.set_graph_options(net, html_fn)

    fd = open(ttl_fn, 'r')
    graph_ttl_str = fd.read()
    fd.close()

    with open(graph_config_fn) as graph_config_fn_f:
        graph_config_obj = json.dumps(json.load(graph_config_fn_f))

    graph_utils.add_js_click_functionality(net, html_fn, graph_ttl_stream=graph_ttl_str, graph_config_obj=graph_config_obj)
    graph_utils.set_html_content(net, html_fn)
    graph_utils.update_js_libraries(html_fn)

    # webbrowser.open('graph_data/graph.html')
    st.components.v1.html(open(html_fn).read(), width=1700, height=1000, scrolling=True)

    st.markdown("***")


if __name__ == '__main__':
    stream_graph()
