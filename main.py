from src.modelagem import criar_modelo

# -------------------------
# Dados do problema
# -------------------------
nodes = list(range(7))
origin = 0
dest = 6

c = [
    [0, 15, 25, 30, 20, 18, 22],
    [15, 0, 28, 33, 22, 20, 25],
    [25, 28, 0, 10, 30, 27, 26],
    [30, 33, 10, 0, 35, 32, 28],
    [20, 22, 30, 35, 0, 12, 18],
    [18, 20, 27, 32, 12, 0, 17],
    [22, 25, 26, 28, 18, 17, 0],
]

s = {0: 0, 1: 60, 2: 60, 3: 40, 4: 45, 5: 50, 6: 0}

def h2m(hhmm):
    h, m = map(int, hhmm.split(":"))
    return h * 60 + m

windows_hours = {
    0: ("08:00", "20:00"),
    1: ("07:00", "18:00"),
    2: ("09:00", "17:00"),
    3: ("09:00", "17:00"),
    4: ("08:00", "19:00"),
    5: ("10:00", "22:00"),
    6: ("06:00", "20:00"),
}

a = {i: h2m(windows_hours[i][0]) for i in nodes}
b = {i: h2m(windows_hours[i][1]) for i in nodes}

# -------------------------
# Criar modelo
# -------------------------
model, x, u, T = criar_modelo(nodes, origin, dest, c, s, a, b)

# Melhorar busca
# model.Params.MIPFocus = 1

# -------------------------
# Resolver
# -------------------------
model.optimize()

def hhmm(m):
    m = int(m)
    return f"{m//60:02d}:{m%60:02d}"

# -------------------------
# Exibir solução
# -------------------------
if model.Status == 2:
    print("\nSolução ótima encontrada!\n")

    # Descobrir sucessores
    succ = {}
    for (i, j), var in x.items():
        if var.X > 0.5:
            succ[i] = j

    # Reconstruir rota
    rota = [origin]
    atual = origin
    while atual != dest:
        atual = succ[atual]
        rota.append(atual)

    print("Rota:", rota)

    print("\nHorários:")
    for i in rota:
        print(f"Nó {i}: {hhmm(T[i].X)} (Ti = {T[i].X:.0f} min)")

else:
    print("Nenhuma solução encontrada. Status:", model.Status)
