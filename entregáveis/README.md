# 📦 Entregáveis — Coleta e Análise de Métricas em Pipeline CI/CD

> Pasta **autossuficiente** para facilitar a correção: contém uma cópia de **todos
> os entregáveis** (relatório, base de dados, gráficos, YAML do pipeline e scripts).
> Os mesmos arquivos também existem em seus locais originais no repositório.

**Aluno:** ryanbotgar
**Repositório:** <https://github.com/ryanbotgar/ci-cd-metrics-experiment>
**Execuções no GitHub Actions:** <https://github.com/ryanbotgar/ci-cd-metrics-experiment/actions>

---

## ✅ Checklist de entregáveis

| # | Entregável | Cópia nesta pasta | Original no repositório |
|---|------------|-------------------|--------------------------|
| 1 | **Link do repositório GitHub** | — | <https://github.com/ryanbotgar/ci-cd-metrics-experiment> |
| 2 | **Arquivo YAML do GitHub Actions** | [`workflow/ci.yml`](./workflow/ci.yml) | [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) |
| 3 | **Script de coleta de métricas** | [`scripts/collect_metrics.py`](./scripts/collect_metrics.py) | [`../scripts/collect_metrics.py`](../scripts/collect_metrics.py) |
| 4 | **Base de dados gerada (CSV/JSON)** | [`data/`](./data) — `metrics.csv`, `runs.csv`, `steps.csv`, `metrics.json` | [`../data/`](../data) |
| 5 | **Gráficos produzidos** | [`charts/`](./charts) — 5 gráficos `.png` | [`../charts/`](../charts) |
| 6 | **Relatório técnico (Markdown)** | [`RELATORIO.md`](./RELATORIO.md) | [`../report/RELATORIO.md`](../report/RELATORIO.md) |
| 7 | **Como reproduzir o experimento** | seção "Como reproduzir" abaixo | [`../README.md`](../README.md) + seção 10 do relatório |

### Scripts (cópia nesta pasta em [`scripts/`](./scripts))

| Script | Função |
|--------|--------|
| [`scripts/collect_metrics.py`](./scripts/collect_metrics.py) | consulta a API do GitHub e produz a base de dados |
| [`scripts/visualize.py`](./scripts/visualize.py) | gera os gráficos a partir da base coletada |
| [`scripts/run_experiment.py`](./scripts/run_experiment.py) | aplica as 14 variações controladas e dispara as execuções (commit+push) |
| [`scripts/gen_tests.py`](./scripts/gen_tests.py) | gera os testes de cada variação a partir das flags |

---

## ▶️ Como reproduzir (resumo)

```bash
git clone https://github.com/ryanbotgar/ci-cd-metrics-experiment
cd ci-cd-metrics-experiment

# disparar as 14 variações (commit+push de cada -> dispara o CI)
python scripts/run_experiment.py --sleep 18

# coletar métricas reais via API do GitHub
pip install -r requirements-analysis.txt
python scripts/collect_metrics.py --repo <OWNER>/<REPO> --workflow ci.yml --limit 30

# gerar os gráficos
python scripts/visualize.py
```

Pré-requisitos: Python 3.10+, `git` e [`gh`](https://cli.github.com/) autenticado.
Detalhes completos na seção 10 do [relatório](./RELATORIO.md).

---

## 📊 Base de dados (`data/metrics.csv`)

Schema exigido pelo enunciado:

```
run_id,commit_sha,commit_message,status,workflow_duration,job_name,job_duration,test_count,test_failures,timestamp
```

Arquivos: [`data/metrics.csv`](./data/metrics.csv) (por job),
[`data/runs.csv`](./data/runs.csv) (agregado por execução, com tempo médio dos testes),
[`data/steps.csv`](./data/steps.csv) (por etapa) e
[`data/metrics.json`](./data/metrics.json) (estrutura completa).

---

## 📈 Gráficos

1. [Tempo total do pipeline por execução](./charts/01_pipeline_duration_por_run.png)
2. [Tempo por job](./charts/02_tempo_por_job.png) · [Tempo por etapa](./charts/02b_tempo_por_step.png)
3. [Taxa de sucesso x falha](./charts/03_taxa_sucesso_falha.png)
4. [Quantidade de testes x duração do pipeline](./charts/04_testes_x_duracao.png)

---

## 🔎 Evidências reais (resumo)

- **15 execuções reais** (run_number 1–15), com `run_id` e `commit_sha` reais — tabela completa na seção 3 do [relatório](./RELATORIO.md).
- IDs reais (exemplos): `27115487508`, `27115557184` (falha), `27115641242` (sequencial), `27115660590` (combo).
- 2 falhas reais induzidas (runs 4 e 5) e variações de cache, paralelismo, volume de testes e teste lento.

> Os dados foram coletados via **API do GitHub** (`scripts/collect_metrics.py`),
> não copiados manualmente da interface.
