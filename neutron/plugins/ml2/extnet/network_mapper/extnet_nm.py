
from extnet_networkcontroller.network_mapper import nm_api


class ExtNetNetworkMapperSP(nm_api.ExtNetNetworkMapper):

    def build_best_path(self, **kwargs):
        graph = kwargs.get('graph')
        start = kwargs.get('start')
        end = kwargs.get('end')

        return find_shortest_path(graph, start, end)


def find_shortest_path(graph, start, end, path=[]):
    path = path + [start]
    if start == end:
        return path
    if start not in graph:
        return None
    shortest = None
    for node in graph[start]:
        if node not in path:
            newpath = find_shortest_path(graph, node, end, path)
            if newpath:
                if not shortest or len(newpath) < len(shortest):
                    shortest = newpath
    return shortest
