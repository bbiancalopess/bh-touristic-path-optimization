# BH Touristic Path Optimization

Sistema de otimização de rotas turísticas para Belo Horizonte utilizando programação linear inteira e a API do Google Maps.

## 📋 Funcionalidades

- Seleção interativa de origem, destino e pontos turísticos intermediários
- Busca inteligente de locais com fuzzy matching
- Integração com Google Maps para buscar locais não cadastrados
- Verificação de duplicatas por proximidade geográfica
- Otimização da rota considerando:
  - Tempo de deslocamento entre locais
  - Tempo de permanência em cada local
  - Horários de funcionamento
- Geração de link do Google Maps com a rota otimizada

## 🚀 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/bh-touristic-path-optimization.git
cd bh-touristic-path-optimization
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite o arquivo .env e adicione sua chave da API do Google Maps
```

5. Instale o Gurobi (necessário licença):
- Visite https://www.gurobi.com/
- Crie uma conta e obtenha uma licença (gratuita para uso acadêmico)
- Instale o Gurobi e configure a licença

## 🎮 Como usar

Execute o programa principal:
```bash
python main.py
```

O sistema irá guiá-lo através dos seguintes passos:
1. Escolha do local de origem
2. Escolha do local de destino
3. Seleção dos pontos turísticos que deseja visitar
4. Definição do tempo de permanência em cada local
5. Otimização e exibição da rota ideal

## 📁 Estrutura do Projeto

```
bh-touristic-path-optimization/
├── main.py                 # Ponto de entrada principal
├── requirements.txt        # Dependências do projeto
├── .env.example           # Exemplo de configuração
└── src/
    ├── datasources/       # Fontes de dados
    │   ├── load_places.py
    │   ├── maps_api.py
    │   └── touristic_spots.csv
    ├── optimization/      # Modelo de otimização
    │   └── optimization_model.py
    ├── routes/           # Geração de rotas
    │   └── google_link.py
    ├── ui/              # Interface do usuário
    │   └── user_interface.py
    └── utils/           # Utilitários
        ├── fuzzy_search.py
        ├── place_resolver.py
        └── time_utils.py
```

## 🔧 Tecnologias Utilizadas

- **Python 3.8+**
- **Gurobi**: Solver de otimização
- **Google Maps API**: Matriz de distâncias e busca de locais
- **RapidFuzz**: Busca fuzzy para matching de nomes
- **python-dotenv**: Gerenciamento de variáveis de ambiente

## 📊 Modelagem Matemática

O problema é modelado como um TSP (Traveling Salesman Problem) aberto com janelas de tempo, utilizando:
- Variáveis binárias para seleção de arestas
- Restrições de grau para garantir rota válida
- Formulação MTZ para eliminação de sub-rotas
- Janelas de tempo para horários de funcionamento
