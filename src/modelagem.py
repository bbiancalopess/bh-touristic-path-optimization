from gurobipy import Model, GRB, quicksum


def criar_modelo(nodes, origin, dest, c, s, a, b, M=1440):

    n = len(nodes)

    # Modelo
    model = Model("Open_TSP_TW_MTZ")

    # Variáveis
    x = {(i, j): model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")
         for i in nodes for j in nodes if i != j}

    u = {i: model.addVar(vtype=GRB.INTEGER, lb=0, ub=n, name=f"u_{i}")
         for i in nodes}

    T = {i: model.addVar(vtype=GRB.INTEGER, lb=0, ub=M, name=f"T_{i}")
         for i in nodes}

    model.update()

    # Fixar posição da origem
    model.addConstr(u[origin] == 0)

    # Objetivo
    model.setObjective(quicksum(c[i][j] * x[i, j] for i, j in x), GRB.MINIMIZE)

    # Restrições de grau — rota aberta 0 → 6

    # Origem: 1 saída, 0 entradas
    model.addConstr(quicksum(x[origin, j] for j in nodes if j != origin) == 1)
    model.addConstr(quicksum(x[i, origin] for i in nodes if i != origin) == 0)

    # Destino: 1 entrada, 0 saídas
    model.addConstr(quicksum(x[i, dest] for i in nodes if i != dest) == 1)
    model.addConstr(quicksum(x[dest, j] for j in nodes if j != dest) == 0)

    # Intermediários: 1 entrada e 1 saída
    for k in nodes:
        if k not in (origin, dest):
            model.addConstr(quicksum(x[k, j] for j in nodes if j != k) == 1)
            model.addConstr(quicksum(x[i, k] for i in nodes if i != k) == 1)

    # MTZ — adaptado para rota aberta
    for i in nodes:
        for j in nodes:
            if i != j:
                model.addConstr(u[i] - u[j] + n * x[i, j] <= n - 1)

    # Sequenciamento temporal
    for i in nodes:
        for j in nodes:
            if i != j:
                model.addConstr(
                    T[j] >= T[i] + s[i] + c[i][j] - M * (1 - x[i, j])
                )

    # Janelas de tempo
    for i in nodes:
        model.addConstr(T[i] >= a[i])
        model.addConstr(T[i] <= b[i] - s[i])

    return model, x, u, T
