# Coleta e Análise de Métricas em Pipeline CI/CD

Experimento prático para **medir e analisar** o comportamento de um pipeline
CI/CD a partir de execuções reais no **GitHub Actions**.

O repositório contém:

- um pequeno projeto Python (`src/calc`) com testes automatizados (`tests/`);
- um pipeline GitHub Actions (`.github/workflows/ci.yml`) com instalação de
  dependências, lint/análise estática, testes, geração de artefatos e coleta de
  métricas;
- um **script de coleta** que consulta a **API do GitHub** e produz uma base de
  dados estruturada (`scripts/collect_metrics.py` → `data/*.csv` e `data/metrics.json`);
- um **script de visualização** que gera os gráficos (`scripts/visualize.py` → `charts/`);
- um **driver** que aplica variações controladas e dispara as execuções
  (`scripts/run_experiment.py`);
- o **relatório técnico** (`report/RELATORIO.md`).

## Estrutura

```
.
├── .github/workflows/ci.yml      # pipeline CI/CD
├── src/calc/                     # biblioteca-alvo
├── tests/                        # testes (base + gerados)
├── experiment/flags.env          # flags da variação atual
├── scripts/
│   ├── gen_tests.py              # gera tests/test_generated.py a partir das flags
│   ├── run_experiment.py         # aplica variações e faz push (dispara o CI)
│   ├── collect_metrics.py        # consulta a API do GitHub -> data/*.csv|json
│   └── visualize.py              # gera os gráficos -> charts/
├── data/                         # base de dados gerada (CSV/JSON)
├── charts/                       # gráficos gerados
└── report/RELATORIO.md           # relatório técnico
```

## Como reproduzir o experimento

Pré-requisitos: Python 3.10+, `git`, [`gh`](https://cli.github.com/) autenticado
(`gh auth login`).

```bash
# 1. Ambiente de desenvolvimento (rodar testes/lint localmente)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python scripts/gen_tests.py
ruff check src tests
pytest --junitxml=junit.xml --json-report --json-report-file=report.json

# 2. Disparar as 14 execuções com variações controladas (faz commit+push em cada)
python scripts/run_experiment.py --sleep 20

# 3. Acompanhar as execuções
gh run list --limit 20

# 4. Coletar as métricas reais via API do GitHub
pip install -r requirements-analysis.txt
python scripts/collect_metrics.py --repo OWNER/REPO --workflow ci.yml --limit 50

# 5. Gerar os gráficos
python scripts/visualize.py
```

## Variações controladas

O `scripts/run_experiment.py` define 14 variações cobrindo: commit com teste
passando, commit com teste falhando, aumento artificial da quantidade de testes,
introdução de teste lento, alteração no cache de dependências e execução com jobs
sequenciais vs paralelos. Veja a tabela completa no relatório.

## Métricas coletadas

`data/metrics.csv` segue o schema:

```
run_id,commit_sha,commit_message,status,workflow_duration,job_name,job_duration,test_count,test_failures,timestamp
```

Também são gerados `data/runs.csv` (agregado por execução), `data/steps.csv`
(por etapa) e `data/metrics.json` (estrutura completa).
