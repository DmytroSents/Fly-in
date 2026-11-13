"""Find paths through the map using BFS and Dijkstra."""

import heapq
from collections import deque
from typing import Optional

from graph import Graph
from header import Zone, ZoneType


class PathFinder:
    """Find paths through a map using different algorithms."""

    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def rebuild_path(
        self, goal: Zone, previous: dict[Zone, Optional[Zone]]
    ) -> list[Zone]:
        # return path by going to zones backwards

        path: list[Zone] = []
        current: Optional[Zone] = goal

        while current is not None:
            path.append(current)
            current = previous[current]

        path.reverse()
        return path

    def bfs_path(self) -> list[Zone]:
        # find a path with the fewest connections using BFS

        start = self.graph.start()
        goal = self.graph.goal()

        visited: set[Zone] = set()
        previous: dict[Zone, Optional[Zone]] = {}
        queue: deque[Zone] = deque()

        visited.add(start)
        previous[start] = None
        queue.append(start)

        while len(queue) > 0:
            current = queue.popleft()

            if current is goal:
                return self.rebuild_path(goal, previous)

            for neighbor in self.graph.neighbors(current):
                if neighbor in visited:
                    continue

                visited.add(neighbor)
                previous[neighbor] = current
                queue.append(neighbor)

        return []

    def cheapest_path(self) -> list[Zone]:
        """Find the path with the lowest movement cost using Dijkstra."""

        start = self.graph.start()
        goal = self.graph.goal()

        # dictionary with Zone : (cost, priority count)
        distances: dict[Zone, tuple[int, int]] = {}

        # dictionary to store Current : Previous
        previous: dict[Zone, Optional[Zone]] = {}

        # queue items [total cost, priority count, zone name, zone obj]
        queue: list[tuple[int, int, str, Zone]] = []

        distances[start] = (0, 0)
        previous[start] = None
        heapq.heappush(queue, (0, 0, start.name, start))

        while len(queue) > 0:
            item = heapq.heappop(queue)

            cost = item[0]
            priority_count = item[1]
            current = item[3]

            # skip previous if cheaper route is found
            if (cost, priority_count) != distances[current]:
                continue

            if current is goal:
                return self.rebuild_path(goal, previous)

            for neighbor in self.graph.neighbors(current):
                new_cost = cost + self.graph.cost_into(neighbor)

                # use negative values to count prio-zones in path
                new_priority_count = priority_count
                if neighbor.zone_type == ZoneType.PRIORITY:
                    new_priority_count -= 1

                new_distance = (new_cost, new_priority_count)
                old_distance = distances.get(neighbor)

                if old_distance is None or new_distance < old_distance:
                    distances[neighbor] = new_distance
                    previous[neighbor] = current

                    heapq.heappush(
                        queue,
                        (new_cost, new_priority_count, neighbor.name, neighbor)
                    )

        return []
