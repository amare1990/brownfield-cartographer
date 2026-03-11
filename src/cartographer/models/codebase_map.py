from pydantic import BaseModel
from typing import List
from .node import ModuleNode, DatasetNode, FunctionNode, TransformationNode

class CodeBaseGraph(BaseModel):
    modules: List[ModuleNode] = []
    datasets: List[DatasetNode] = []
    functions: List[FunctionNode] = []
    transformations: List[TransformationNode] = []
