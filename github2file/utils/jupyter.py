import nbformat
from nbconvert import PythonExporter

def convert_ipynb_to_py(ipynb_content):
    notebook = nbformat.reads(ipynb_content, as_version=4)
    exporter = PythonExporter()
    (body, _) = exporter.from_notebook_node(notebook)
    return body

