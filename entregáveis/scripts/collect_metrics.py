#!/usr/bin/env python3
"""Coleta métricas reais de execução do pipeline via API do GitHub.

Para cada execução (workflow run) do workflow CI, o script:
  1. lê os metadados do run (status, sha, mensagem do commit, timestamps);
  2. lê os jobs e steps (com início/fim) -> durações;
  3. baixa o artefato ``test-results`` e lê ``report.json`` (pytest-json-report)
     para extrair quantidade de testes, falhas e tempo médio dos testes.

Saídas em ``data/``:
  * ``metrics.csv``  -> uma linha por (run, job) seguindo o schema pedido:
        run_id,commit_sha,commit_message,status,workflow_duration,
        job_name,job_duration,test_count,test_failures,timestamp
  * ``runs.csv``     -> uma linha por run (agregado)
  * ``steps.csv``    -> uma linha por step
  * ``metrics.json`` -> estrutura completa aninhada

Autenticação: usa GITHUB_TOKEN do ambiente; se ausente, tenta ``gh auth token``.

Uso:
    python scripts/collect_metrics.py --repo OWNER/REPO [--workflow ci.yml] [--limit 50]
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
API = "https://api.github.com"


def get_token() -> str:
    import os

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token
    try:
        out = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, check=True
        )
        return out.stdout.strip()
    except Exception as exc:  # noqa: BLE001
        sys.exit(f"Não foi possível obter token do GitHub: {exc}")


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def duration_seconds(start: str | None, end: str | None) -> float | None:
    s, e = parse_dt(start), parse_dt(end)
    if s and e:
        return round((e - s).total_seconds(), 3)
    return None


class GitHub:
    def __init__(self, token: str, repo: str):
        self.repo = repo
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

    def get(self, path: str, **params):
        url = path if path.startswith("http") else f"{API}{path}"
        resp = self.session.get(url, params=params or None)
        resp.raise_for_status()
        return resp

    def list_runs(self, workflow: str | None, limit: int) -> list[dict]:
        if workflow:
            path = f"/repos/{self.repo}/actions/workflows/{workflow}/runs"
        else:
            path = f"/repos/{self.repo}/actions/runs"
        runs: list[dict] = []
        page = 1
        while len(runs) < limit:
            resp = self.get(path, per_page=100, page=page)
            batch = resp.json().get("workflow_runs", [])
            if not batch:
                break
            runs.extend(batch)
            page += 1
        return runs[:limit]

    def list_jobs(self, run_id: int) -> list[dict]:
        resp = self.get(f"/repos/{self.repo}/actions/runs/{run_id}/jobs", per_page=100)
        return resp.json().get("jobs", [])

    def list_artifacts(self, run_id: int) -> list[dict]:
        resp = self.get(f"/repos/{self.repo}/actions/runs/{run_id}/artifacts", per_page=100)
        return resp.json().get("artifacts", [])

    def download_artifact_zip(self, artifact: dict) -> bytes | None:
        url = artifact.get("archive_download_url")
        if not url:
            return None
        resp = self.session.get(url)
        if resp.status_code != 200:
            return None
        return resp.content


def parse_test_report(zip_bytes: bytes) -> dict | None:
    """Extrai métricas de teste do report.json (pytest-json-report) num zip."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile:
        return None
    name = next((n for n in zf.namelist() if n.endswith("report.json")), None)
    if not name:
        return None
    data = json.loads(zf.read(name))
    summary = data.get("summary", {})
    tests = data.get("tests", [])
    durations = [t.get("call", {}).get("duration", t.get("duration", 0)) for t in tests]
    durations = [d for d in durations if isinstance(d, (int, float))]
    return {
        "test_count": summary.get("total", len(tests)),
        "test_failures": summary.get("failed", 0),
        "test_passed": summary.get("passed", 0),
        "test_mean_duration": round(mean(durations), 4) if durations else 0.0,
        "tests_total_duration": round(sum(durations), 4) if durations else 0.0,
    }


def collect(repo: str, workflow: str | None, limit: int) -> dict:
    gh = GitHub(get_token(), repo)
    runs = gh.list_runs(workflow, limit)
    print(f"Encontrados {len(runs)} runs em {repo}")

    result_runs: list[dict] = []
    for run in runs:
        run_id = run["id"]
        wf_duration = duration_seconds(
            run.get("run_started_at"), run.get("updated_at")
        )
        commit_message = (run.get("head_commit") or {}).get("message", "")
        commit_message = commit_message.splitlines()[0] if commit_message else ""

        jobs = gh.list_jobs(run_id)
        job_rows = []
        for job in jobs:
            steps = [
                {
                    "name": s.get("name"),
                    "status": s.get("conclusion"),
                    "duration": duration_seconds(s.get("started_at"), s.get("completed_at")),
                }
                for s in job.get("steps", [])
            ]
            job_rows.append(
                {
                    "job_name": job.get("name"),
                    "status": job.get("conclusion"),
                    "job_duration": duration_seconds(
                        job.get("started_at"), job.get("completed_at")
                    ),
                    "started_at": job.get("started_at"),
                    "completed_at": job.get("completed_at"),
                    "steps": steps,
                }
            )

        # Métricas de teste a partir do artefato.
        test_metrics = {
            "test_count": None,
            "test_failures": None,
            "test_passed": None,
            "test_mean_duration": None,
            "tests_total_duration": None,
        }
        for art in gh.list_artifacts(run_id):
            if art.get("name") == "test-results" and not art.get("expired"):
                blob = gh.download_artifact_zip(art)
                if blob:
                    parsed = parse_test_report(blob)
                    if parsed:
                        test_metrics.update(parsed)
                break

        result_runs.append(
            {
                "run_id": run_id,
                "run_number": run.get("run_number"),
                "commit_sha": run.get("head_sha"),
                "commit_message": commit_message,
                "status": run.get("conclusion") or run.get("status"),
                "event": run.get("event"),
                "workflow_duration": wf_duration,
                "created_at": run.get("created_at"),
                "run_started_at": run.get("run_started_at"),
                "updated_at": run.get("updated_at"),
                "html_url": run.get("html_url"),
                "attempt": run.get("run_attempt"),
                "jobs": job_rows,
                **test_metrics,
            }
        )

    collected_at = datetime.now(timezone.utc).isoformat()
    return {"repo": repo, "collected_at": collected_at, "runs": result_runs}


def write_outputs(payload: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    (DATA_DIR / "metrics.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    # metrics.csv -> uma linha por (run, job), schema pedido pelo enunciado.
    schema = [
        "run_id",
        "commit_sha",
        "commit_message",
        "status",
        "workflow_duration",
        "job_name",
        "job_duration",
        "test_count",
        "test_failures",
        "timestamp",
    ]
    with (DATA_DIR / "metrics.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(schema)
        for run in payload["runs"]:
            for job in run["jobs"]:
                w.writerow(
                    [
                        run["run_id"],
                        run["commit_sha"],
                        run["commit_message"],
                        run["status"],
                        run["workflow_duration"],
                        job["job_name"],
                        job["job_duration"],
                        run["test_count"],
                        run["test_failures"],
                        run["run_started_at"],
                    ]
                )

    # runs.csv -> agregado por run.
    run_cols = [
        "run_id",
        "run_number",
        "commit_sha",
        "commit_message",
        "status",
        "event",
        "workflow_duration",
        "test_count",
        "test_failures",
        "test_passed",
        "test_mean_duration",
        "attempt",
        "run_started_at",
        "updated_at",
        "html_url",
    ]
    with (DATA_DIR / "runs.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=run_cols, extrasaction="ignore")
        w.writeheader()
        for run in payload["runs"]:
            w.writerow(run)

    # steps.csv -> uma linha por step.
    with (DATA_DIR / "steps.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run_id", "job_name", "step_name", "status", "step_duration"])
        for run in payload["runs"]:
            for job in run["jobs"]:
                for step in job["steps"]:
                    w.writerow(
                        [
                            run["run_id"],
                            job["job_name"],
                            step["name"],
                            step["status"],
                            step["duration"],
                        ]
                    )

    print(f"Escrito: {DATA_DIR/'metrics.csv'}")
    print(f"Escrito: {DATA_DIR/'runs.csv'}")
    print(f"Escrito: {DATA_DIR/'steps.csv'}")
    print(f"Escrito: {DATA_DIR/'metrics.json'}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, help="OWNER/REPO")
    ap.add_argument("--workflow", default="ci.yml", help="arquivo do workflow (default: ci.yml)")
    ap.add_argument("--limit", type=int, default=50, help="máximo de runs a coletar")
    args = ap.parse_args()

    payload = collect(args.repo, args.workflow, args.limit)
    write_outputs(payload)


if __name__ == "__main__":
    main()
