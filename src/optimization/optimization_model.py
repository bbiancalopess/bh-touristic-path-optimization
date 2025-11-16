"""Optimization model for the Touristic Path Problem with Time Windows."""

from gurobipy import Model, GRB, quicksum
from typing import List, Dict, Tuple


def create_optimization_model(
    nodes: List[int],
    origin_index: int,
    destination_index: int,
    travel_times: List[List[int]],
    stay_times: Dict[int, int],
    opening_times: Dict[int, int],
    closing_times: Dict[int, int],
    max_time: int = 1440,
    start_time: int = 0
) -> Tuple[Model, Dict, Dict, Dict]:
    """
    Create the optimization model for the Open TSP with Time Windows using MTZ formulation.
    
    Args:
        nodes: List of node indices
        origin_index: Index of the origin node
        destination_index: Index of the destination node
        travel_times: Matrix of travel times between nodes (in minutes)
        stay_times: Dictionary mapping node index to stay time (in minutes)
        opening_times: Dictionary mapping node index to opening time (minutes from midnight)
        closing_times: Dictionary mapping node index to closing time (minutes from midnight)
        max_time: Maximum time for the route (default: 1440 minutes = 24 hours)
        start_time: Starting time for the route (minutes from midnight, default: 0)
    
    Returns:
        Tuple of (model, x_vars, u_vars, T_vars) where:
        - model: Gurobi model object
        - x_vars: Binary variables indicating if edge (i,j) is used
        - u_vars: Integer variables for MTZ subtour elimination
        - T_vars: Integer variables for arrival times at each node
    """

    num_nodes = len(nodes)

    # Create model
    model = Model("Open_TSP_TW_MTZ")

    # Decision variables
    # x[i,j] = 1 if edge from node i to node j is used
    x_vars = {(i, j): model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")
              for i in nodes for j in nodes if i != j}

    # u[i] = position of node i in the route (for MTZ subtour elimination)
    u_vars = {i: model.addVar(vtype=GRB.INTEGER, lb=0, ub=num_nodes, name=f"u_{i}")
              for i in nodes}

    # T[i] = arrival time at node i
    T_vars = {i: model.addVar(vtype=GRB.INTEGER, lb=0, ub=max_time, name=f"T_{i}")
              for i in nodes}

    model.update()

    # Fix origin position
    model.addConstr(u_vars[origin_index] == 0)

    # Objective: minimize total travel time
    model.setObjective(
        quicksum(travel_times[i][j] * x_vars[i, j] for i, j in x_vars),
        GRB.MINIMIZE
    )

    # Degree constraints for open route

    # Origin: exactly 1 outgoing edge, 0 incoming edges
    model.addConstr(quicksum(x_vars[origin_index, j] for j in nodes if j != origin_index) == 1)
    model.addConstr(quicksum(x_vars[i, origin_index] for i in nodes if i != origin_index) == 0)

    # Destination: exactly 1 incoming edge, 0 outgoing edges
    model.addConstr(quicksum(x_vars[i, destination_index] for i in nodes if i != destination_index) == 1)
    model.addConstr(quicksum(x_vars[destination_index, j] for j in nodes if j != destination_index) == 0)

    # Intermediate nodes: exactly 1 incoming and 1 outgoing edge
    for k in nodes:
        if k not in (origin_index, destination_index):
            model.addConstr(quicksum(x_vars[k, j] for j in nodes if j != k) == 1)
            model.addConstr(quicksum(x_vars[i, k] for i in nodes if i != k) == 1)

        # Time window constraints
        model.addConstr(T_vars[k] >= opening_times[k])
        model.addConstr(T_vars[k] <= closing_times[k] - stay_times[k])

    # MTZ subtour elimination constraints (adapted for open route)
    for i in nodes:
        for j in nodes:
            if i != j:
                # MTZ subtour elimination constraints (adapted for open route)
                model.addConstr(
                    u_vars[i] - u_vars[j] + num_nodes * x_vars[i, j] <= num_nodes - 1
                )

                # Time sequencing constraints
                model.addConstr(
                    T_vars[j] >= T_vars[i] + stay_times[i] + travel_times[i][j] - max_time * (1 - x_vars[i, j])
                )

    # Start time constraint for origin
    model.addConstr(T_vars[origin_index] >= start_time)

    return model, x_vars, u_vars, T_vars
