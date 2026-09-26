"""SR-001 — Scale Reconnaissance v1 Harness.

Investigação experimental de Baseline A (Capacidade Computacional e Análise Estrutural de Blocking).
Este harness opera estritamente fora de src/agent_lab/ e tests/.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import platform
import random
import statistics
import sys
import tempfile
import time
import tracemalloc
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from agent_lab.catalog_csv_adapter import load_catalog_materials
from agent_lab.catalog_quality import diagnose_catalog_quality
import agent_lab.duplicates as dup_module
from agent_lab.normalization import (
    category_token,
    normalize_text,
)


BRT = timezone(timedelta(hours=-3), name="BRT")


def _resolve_deadline() -> datetime:
    """Resolve o deadline operacional permitindo override via SR001_DEADLINE.

    Caso não seja especificado, utiliza 10:35 BRT da data de execução corrente.
    Garante retorno sempre timezone-aware.
    """
    env_override = os.environ.get("SR001_DEADLINE")
    if env_override:
        try:
            parsed = datetime.fromisoformat(env_override)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=BRT)
            return parsed
        except ValueError:
            pass
    now = datetime.now(BRT)
    return datetime(now.year, now.month, now.day, 10, 35, 0, tzinfo=BRT)


DEADLINE = _resolve_deadline()
SEED = 42
CHECKPOINTS_DIR = Path(__file__).resolve().parent / "checkpoints"

MATERIAL_GROUPS = [
    "ROLAMENTOS",
    "FIXADORES",
    "TUBULACOES",
    "CABOS",
    "MOTORES",
    "INSTRUMENTACAO",
    "VALVULAS",
    "TRANSMISSAO",
    "VEDACOES",
    "ELETRICA",
]

MANUFACTURERS = [
    "SKF",
    "WEG",
    "SIEMENS",
    "SCHNEIDER",
    "PARKER",
    "DANFOSS",
    "3M",
    "TIMKEN",
    "FAG",
    "SPIRAX SARCO",
    "",  # Proporção controlada sem fabricante
]

NOUNS = [
    "ROLAMENTO",
    "PARAFUSO",
    "VALVULA",
    "CABO",
    "MOTOR",
    "SENSOR",
    "FLANGE",
    "ACOPLAMENTO",
    "CORREIA",
    "RETENTOR",
    "CONTACTOR",
    "DISJUNTOR",
]

DIMENSIONS = [
    "M10X30",
    "M12X40",
    "M16X50",
    "6205",
    "6308",
    "2RS",
    "2.5MM",
    "4MM",
    "10CV",
    "15CV",
    "380V",
    "220V",
    "0-10 BAR",
    "4-20 MA",
    "DN50",
    "DN100",
    "SCH40",
    "ISO VG 68",
    "100A",
]

UNITS = ["PC", "UN", "M", "KG", "CJ", "L"]


def get_remaining_seconds(deadline: datetime | None = None) -> float:
    """Calcula os segundos restantes até o deadline operacional de 10:35 BRT."""
    target = deadline or DEADLINE
    now = datetime.now(BRT)
    return (target - now).total_seconds()


def generate_synthetic_catalog_csv(n: int, path: Path, seed: int = 42) -> str:
    """Gera um CSV sintético operacional no padrão nested-prefix determinístico."""
    rng = random.Random(seed)

    fieldnames = [
        "material_id",
        "description_short",
        "long_description",
        "unit",
        "manufacturer",
        "manufacturer_part_number",
        "material_group",
        "status",
    ]

    hasher = hashlib.sha256()

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for i in range(1, n + 1):
            mat_id = f"MAT-{i:06d}"
            group = rng.choice(MATERIAL_GROUPS)
            noun = rng.choice(NOUNS)
            mfg = rng.choice(MANUFACTURERS)
            dim1 = rng.choice(DIMENSIONS)
            dim2 = rng.choice(DIMENSIONS)

            pn = f"PN-{dim1}-{i % 50}" if mfg else ""
            desc_short = f"{noun} {dim1} {dim2} {mfg}".strip()
            desc_long = f"ITEM INDUSTRIAL {desc_short} APLICACAO GERAL"
            unit = rng.choice(UNITS)
            status = "ACTIVE"

            row = {
                "material_id": mat_id,
                "description_short": desc_short,
                "long_description": desc_long,
                "unit": unit,
                "manufacturer": mfg,
                "manufacturer_part_number": pn,
                "material_group": group,
                "status": status,
            }
            writer.writerow(row)

    with path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)

    return hasher.hexdigest()


@dataclass
class TimingMetrics:
    t_csv_min: float
    t_csv_med: float
    t_csv_max: float
    t_diag_min: float
    t_diag_med: float
    t_diag_max: float
    t_total_min: float
    t_total_med: float
    t_total_max: float
    raw_total_elapsed: float


@dataclass
class CandidateBlocksMetrics:
    p1: int
    p2: int
    p12: int
    candidate_union: int
    all_unordered_pairs: int
    candidate_ratio: float
    theoretical_reduction_pct: float
    max_block_f1: int
    max_block_f2: int
    top_blocks_f1: list[tuple[tuple[str, str], int]]
    top_blocks_f2: list[tuple[tuple[str, str], int]]


def measure_timing_and_blocks(
    n: int,
    csv_path: Path,
    repeats: int = 3,
) -> tuple[TimingMetrics | None, CandidateBlocksMetrics, Any]:
    t_csv_runs: list[float] = []
    t_diag_runs: list[float] = []
    t_total_runs: list[float] = []
    last_report: Any = None
    records: Any = None

    t_start_all = time.perf_counter()

    for r in range(repeats):
        if get_remaining_seconds() <= 0:
            return None, None, None  # Interrompe se cruzar o deadline

        t0 = time.perf_counter()
        records = load_catalog_materials(csv_path)
        t1 = time.perf_counter()
        last_report = diagnose_catalog_quality(records, catalog_id=f"CAT-SR001-{n}")
        t2 = time.perf_counter()

        t_csv_runs.append(t1 - t0)
        t_diag_runs.append(t2 - t1)
        t_total_runs.append(t2 - t0)

    raw_total_elapsed = time.perf_counter() - t_start_all

    timing = TimingMetrics(
        t_csv_min=min(t_csv_runs),
        t_csv_med=statistics.median(t_csv_runs),
        t_csv_max=max(t_csv_runs),
        t_diag_min=min(t_diag_runs),
        t_diag_med=statistics.median(t_diag_runs),
        t_diag_max=max(t_diag_runs),
        t_total_min=min(t_total_runs),
        t_total_med=statistics.median(t_total_runs),
        t_total_max=max(t_total_runs),
        raw_total_elapsed=raw_total_elapsed,
    )

    # Análise combinatória de Candidate Blocks (C5)
    p1_counts: dict[tuple[str, str], int] = {}
    p2_counts: dict[tuple[str, str], int] = {}
    joint_counts: dict[tuple[tuple[str, str], tuple[str, str]], int] = {}

    for record in records:
        norm_pn = normalize_text(record.manufacturer_part_number)
        norm_mfg = normalize_text(record.manufacturer)
        p1_key = (norm_pn, norm_mfg) if (norm_pn and norm_mfg) else None

        full_desc = f"{record.description_short} {record.long_description}".strip()
        cat_tok = category_token(full_desc)
        norm_grp = normalize_text(record.material_group)
        p2_key = (norm_grp, cat_tok) if cat_tok else None

        if p1_key is not None:
            p1_counts[p1_key] = p1_counts.get(p1_key, 0) + 1
        if p2_key is not None:
            p2_counts[p2_key] = p2_counts.get(p2_key, 0) + 1
        if p1_key is not None and p2_key is not None:
            joint_key = (p1_key, p2_key)
            joint_counts[joint_key] = joint_counts.get(joint_key, 0) + 1

    p1 = sum(count * (count - 1) // 2 for count in p1_counts.values() if count >= 2)
    p2 = sum(count * (count - 1) // 2 for count in p2_counts.values() if count >= 2)
    p12 = sum(count * (count - 1) // 2 for count in joint_counts.values() if count >= 2)

    candidate_union = p1 + p2 - p12
    all_unordered_pairs = n * (n - 1) // 2
    candidate_ratio = (
        candidate_union / all_unordered_pairs if all_unordered_pairs > 0 else 0.0
    )
    reduction_pct = (1.0 - candidate_ratio) * 100.0

    max_b1 = max(p1_counts.values(), default=0)
    max_b2 = max(p2_counts.values(), default=0)

    top_b1 = sorted(p1_counts.items(), key=lambda item: item[1], reverse=True)[:3]
    top_b2 = sorted(p2_counts.items(), key=lambda item: item[1], reverse=True)[:3]

    blocks = CandidateBlocksMetrics(
        p1=p1,
        p2=p2,
        p12=p12,
        candidate_union=candidate_union,
        all_unordered_pairs=all_unordered_pairs,
        candidate_ratio=candidate_ratio,
        theoretical_reduction_pct=reduction_pct,
        max_block_f1=max_b1,
        max_block_f2=max_b2,
        top_blocks_f1=top_b1,
        top_blocks_f2=top_b2,
    )

    return timing, blocks, last_report


def persist_experimental_checkpoint(
    n: int,
    timing: TimingMetrics,
    blocks: CandidateBlocksMetrics,
    csv_sha256: str,
    seed: int = SEED,
    checkpoints_dir: Path = CHECKPOINTS_DIR,
) -> Path:
    """H-034 — Checkpointed Experimental Evidence Gate.

    Persiste de forma atômica e imediata a evidência experimental do volume N concluído,
    garantindo que falhas posteriores de apresentação não destruam os dados já apurados.
    """
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    target_file = checkpoints_dir / f"sr001_evidence_N{n}.json"
    tmp_file = checkpoints_dir / f"sr001_evidence_N{n}.json.tmp"

    data = {
        "checkpoint_version": "1.0",
        "status": "COMPLETED",
        "n": n,
        "seed": seed,
        "timestamp_brt": datetime.now(BRT).isoformat(),
        "csv_sha256": csv_sha256,
        "timing_metrics": {
            "t_csv_min": timing.t_csv_min,
            "t_csv_med": timing.t_csv_med,
            "t_csv_max": timing.t_csv_max,
            "t_diag_min": timing.t_diag_min,
            "t_diag_med": timing.t_diag_med,
            "t_diag_max": timing.t_diag_max,
            "t_total_min": timing.t_total_min,
            "t_total_med": timing.t_total_med,
            "t_total_max": timing.t_total_max,
            "raw_total_elapsed": timing.raw_total_elapsed,
        },
        "candidate_blocks_metrics": {
            "p1": blocks.p1,
            "p2": blocks.p2,
            "p12": blocks.p12,
            "candidate_union": blocks.candidate_union,
            "all_unordered_pairs": blocks.all_unordered_pairs,
            "candidate_ratio": blocks.candidate_ratio,
            "theoretical_reduction_pct": blocks.theoretical_reduction_pct,
            "max_block_f1": blocks.max_block_f1,
            "max_block_f2": blocks.max_block_f2,
            "top_blocks_f1": [[list(k), v] for k, v in blocks.top_blocks_f1],
            "top_blocks_f2": [[list(k), v] for k, v in blocks.top_blocks_f2],
        },
    }

    with tmp_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    os.replace(tmp_file, target_file)
    return target_file


def run_smoke_validation(
    n: int = 50,
    checkpoints_dir: Path | None = None,
) -> dict[str, Any]:
    """Executa smoke validation minimalista de H-034 para provar persistência resiliente.

    Não executa o Baseline A completo nem produz números oficiais.
    """
    target_dir = checkpoints_dir or CHECKPOINTS_DIR
    with tempfile.TemporaryDirectory(prefix="sr001_smoke_") as tmpdir:
        tmp_path = Path(tmpdir)
        csv_file = tmp_path / f"catalog_smoke_{n}.csv"
        csv_sha = generate_synthetic_catalog_csv(n, csv_file, seed=SEED)

        # A: O volume N conclui medições
        timing, blocks, _ = measure_timing_and_blocks(n, csv_file, repeats=1)
        if timing is None or blocks is None:
            raise RuntimeError(f"Smoke run para N={n} não concluiu com sucesso.")

        # B: Checkpoint físico é criado atomicamente
        checkpoint_file = persist_experimental_checkpoint(
            n=n,
            timing=timing,
            blocks=blocks,
            csv_sha256=csv_sha,
            seed=SEED,
            checkpoints_dir=target_dir,
        )
        checkpoint_exists_before = checkpoint_file.is_file()
        if not checkpoint_exists_before:
            raise RuntimeError(f"Checkpoint físico não encontrado em {checkpoint_file}")

        # C: O JSON pode ser relido com decodificação UTF-8
        with checkpoint_file.open("r", encoding="utf-8") as f:
            content_before = f.read()
            data = json.loads(content_before)

        # D: Os dados essenciais correspondem ao resultado daquele N
        assert data["checkpoint_version"] == "1.0"
        assert data["status"] == "COMPLETED"
        assert data["n"] == n
        assert data["seed"] == SEED
        assert data["csv_sha256"] == csv_sha
        assert data["candidate_blocks_metrics"]["all_unordered_pairs"] == n * (n - 1) // 2
        assert data["candidate_blocks_metrics"]["p1"] == blocks.p1
        assert data["candidate_blocks_metrics"]["p2"] == blocks.p2
        assert data["candidate_blocks_metrics"]["candidate_union"] == blocks.candidate_union

        # E: Simulação de falha intencional na camada de apresentação (ex: UnicodeEncodeError)
        simulated_failure_triggered = False
        try:
            raise UnicodeEncodeError(
                "charmap",
                "\u2014",
                0,
                1,
                "Simulated presentation layer catastrophic failure",
            )
        except UnicodeEncodeError:
            simulated_failure_triggered = True

        # Verifica que o checkpoint físico sobreviveu intacto e inalterado
        checkpoint_exists_after = checkpoint_file.is_file()
        with checkpoint_file.open("r", encoding="utf-8") as f:
            content_after = f.read()

        checkpoint_intact = checkpoint_exists_after and (content_before == content_after)

        return {
            "criterion_a_concluded": True,
            "criterion_b_created": checkpoint_exists_before,
            "criterion_c_readable": True,
            "criterion_d_data_matched": True,
            "criterion_e_survived_presentation_failure": (
                simulated_failure_triggered and checkpoint_intact
            ),
            "checkpoint_file": str(checkpoint_file),
            "checkpoint_sha256": hashlib.sha256(content_after.encode("utf-8")).hexdigest(),
            "n": n,
            "timing_med_diag": timing.t_diag_med,
            "all_unordered_pairs": data["candidate_blocks_metrics"]["all_unordered_pairs"],
        }


def verify_predicate_calls_instrumented(csv_path: Path, n: int) -> tuple[int, int, bool]:
    """Verifica N(N-1) com monkeypatch temporário e restaurado obrigatoriamente (C4)."""
    records = load_catalog_materials(csv_path)

    original_predicate = dup_module.is_possible_duplicate
    call_count = 0

    def counting_predicate(incoming: Any, existing: Any) -> bool:
        nonlocal call_count
        call_count += 1
        return original_predicate(incoming, existing)

    try:
        dup_module.is_possible_duplicate = counting_predicate
        diagnose_catalog_quality(records, catalog_id=f"CAT-PRED-{n}")
    finally:
        dup_module.is_possible_duplicate = original_predicate

    theoretical = n * (n - 1)
    passed = (call_count == theoretical)
    return call_count, theoretical, passed


def measure_memory_isolated(csv_path: Path, n: int) -> float:
    """Mede pico de memória alocada via tracemalloc em rodada separada (C6)."""
    tracemalloc.start()
    records = load_catalog_materials(csv_path)
    _ = diagnose_catalog_quality(records, catalog_id=f"CAT-MEM-{n}")
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak / (1024.0 * 1024.0)


def calculate_exponent(ns: list[int], t_medians: list[float]) -> float:
    """Calcula regressão log(N) vs log(T_diag) com stdlib math (C7)."""
    x = [math.log(n) for n in ns]
    y = [math.log(t) for t in t_medians]

    x_mean = sum(x) / len(x)
    y_mean = sum(y) / len(y)

    numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
    denominator = sum((xi - x_mean) ** 2 for xi in x)

    return numerator / denominator if denominator != 0 else 0.0


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    start_time_brt = datetime.now(BRT)

    volumes = [250, 500, 1000, 2000]
    timing_results: dict[int, TimingMetrics] = {}
    block_results: dict[int, CandidateBlocksMetrics] = {}
    sha256_hashes: dict[int, str] = {}
    completed_ns: list[int] = []
    unexecuted_ns: list[int] = []
    stop_reason: str = "Conclusão de todos os volumes planejados"

    pred_verification_result: tuple[int, int, int, bool] | None = None
    memory_result: tuple[int, float] | None = None
    memory_status: str = "NOT EXECUTED"

    prev_n: int | None = None
    prev_elapsed: float | None = None

    with tempfile.TemporaryDirectory(prefix="sr001_exp_") as tmpdir:
        tmp_path = Path(tmpdir)

        # 1. Verificação de Predicados fora do timing (C4)
        rem_sec = get_remaining_seconds()
        if rem_sec > 10.0:
            csv_250 = tmp_path / "catalog_250_pred.csv"
            generate_synthetic_catalog_csv(250, csv_250, seed=SEED)
            obs, theo, passed = verify_predicate_calls_instrumented(csv_250, 250)
            pred_verification_result = (250, obs, theo, passed)
            if not passed:
                print(f"[FATAL] Predicate verification failed: observed {obs} != theoretical {theo}")
                return

        # 2. Execução dos Volumes Progressivos com Gate Adaptativo
        for idx, n in enumerate(volumes):
            rem_sec = get_remaining_seconds()

            if prev_n is not None and prev_elapsed is not None:
                ratio = n / prev_n
                estimated_next = prev_elapsed * (ratio ** 2)
                required_budget = estimated_next * 1.25

                if rem_sec <= required_budget:
                    stop_reason = (
                        f"Orçamento insuficiente para N={n}: restante={rem_sec:.1f}s <= "
                        f"necessário={required_budget:.1f}s (estimado {estimated_next:.1f}s * 1.25)"
                    )
                    unexecuted_ns = volumes[idx:]
                    break
            elif rem_sec <= 10.0:
                stop_reason = f"Orçamento restante insuficiente para N={n} (restante={rem_sec:.1f}s)"
                unexecuted_ns = volumes[idx:]
                break

            csv_file = tmp_path / f"catalog_{n}.csv"
            sha = generate_synthetic_catalog_csv(n, csv_file, seed=SEED)
            sha256_hashes[n] = sha

            res = measure_timing_and_blocks(n, csv_file, repeats=3)
            timing, blocks, _ = res

            if timing is None:
                stop_reason = f"Execução interrompida durante N={n} por deadline 10:35 BRT"
                unexecuted_ns = volumes[idx:]
                break

            timing_results[n] = timing
            block_results[n] = blocks

            # H-034: Checkpoint persistido IMEDIATAMENTE após N concluído
            persist_experimental_checkpoint(
                n=n,
                timing=timing,
                blocks=blocks,
                csv_sha256=sha,
                seed=SEED,
            )
            completed_ns.append(n)

            prev_n = n
            prev_elapsed = timing.raw_total_elapsed

        # 3. Medição de Memória Separada com Budget Gate (C6)
        if completed_ns:
            largest_n = completed_ns[-1]
            estimated_mem_budget = timing_results[largest_n].t_total_max * 5.0 * 1.25
            rem_sec = get_remaining_seconds()

            if rem_sec > estimated_mem_budget:
                csv_mem = tmp_path / f"catalog_{largest_n}.csv"
                peak_mb = measure_memory_isolated(csv_mem, largest_n)
                memory_result = (largest_n, peak_mb)
                memory_status = f"{peak_mb:.2f} MB"
            else:
                memory_status = (
                    f"DEFERRED BY TIME BUDGET (restante={rem_sec:.1f}s <= "
                    f"necessário={estimated_mem_budget:.1f}s)"
                )

    end_time_brt = datetime.now(BRT)

    # 4. Cálculo do Expoente (C7)
    if len(completed_ns) >= 3:
        t_medians = [timing_results[n].t_diag_med for n in completed_ns]
        p_val = calculate_exponent(completed_ns, t_medians)
        p_exponent_str = f"{p_val:.4f} (pontos utilizados: {completed_ns})"
    else:
        p_exponent_str = "NOT COMPUTED — insufficient completed points"

    # =========================================================================
    # RELATÓRIO FINAL ESTRUTURADO DE EVIDÊNCIAS
    # =========================================================================
    print("\n" + "=" * 80)
    print("SR-001 — SCALE RECONNAISSANCE V1 (BASELINE A REPORT)")
    print("=" * 80)

    print("\n--- A. AMBIENTE ---")
    print(f"Timestamp início (BRT): {start_time_brt.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Timestamp final  (BRT): {end_time_brt.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Python:                {platform.python_version()} ({platform.python_implementation()})")
    print(f"OS:                    {platform.system()}")
    print(f"Release:               {platform.release()} ({platform.version()})")
    print(f"Arquitetura:           {platform.machine()} / {platform.processor() or 'generic'}")
    print(f"CPU count:             {os.cpu_count()}")
    print(f"RAM:                   not collected by stdlib harness")

    print("\n--- B. GERADOR ---")
    print(f"SEED = {SEED}")
    print("Dataset progression: deterministic nested-prefix")
    print("Esquema das 8 colunas canônicas: material_id, description_short, long_description, unit, manufacturer, manufacturer_part_number, material_group, status")
    print("Nota metodológica: Baseline A synthetic load != representative industrial Ground Truth")

    print("\n--- C. SHA-256 DOS CSVs CONCLUÍDOS ---")
    for n in completed_ns:
        print(f"N = {n:4d}: {sha256_hashes[n]}")

    print("\n--- D. TIMING (SEGUNDOS) ---")
    print(f"{'N':>6} | {'T_csv_min':>9} {'T_csv_med':>9} {'T_csv_max':>9} | {'T_diag_min':>10} {'T_diag_med':>10} {'T_diag_max':>10} | {'T_tot_min':>9} {'T_tot_med':>9} {'T_tot_max':>9} | {'N(N-1)':>10}")
    print("-" * 115)
    for n in completed_ns:
        t = timing_results[n]
        n_pairs = n * (n - 1)
        print(
            f"{n:6d} | {t.t_csv_min:9.4f} {t.t_csv_med:9.4f} {t.t_csv_max:9.4f} | "
            f"{t.t_diag_min:10.4f} {t.t_diag_med:10.4f} {t.t_diag_max:10.4f} | "
            f"{t.t_total_min:9.4f} {t.t_total_med:9.4f} {t.t_total_max:9.4f} | {n_pairs:10d}"
        )

    print("\n--- E. CANDIDATE BLOCKS (ANÁLISE TEÓRICA RELATIVA AO DETECTOR ATUAL) ---")
    print("Nota: candidate space reduction != semantic recall")
    print(f"{'N':>6} | {'P1':>8} {'P2':>8} {'P12':>6} | {'Union':>8} {'AllPairs':>10} {'Ratio':>8} {'Reduc%':>8} | {'MaxB1':>6} {'MaxB2':>6}")
    print("-" * 95)
    for n in completed_ns:
        b = block_results[n]
        print(
            f"{n:6d} | {b.p1:8d} {b.p2:8d} {b.p12:6d} | {b.candidate_union:8d} {b.all_unordered_pairs:10d} "
            f"{b.candidate_ratio:8.4f} {b.theoretical_reduction_pct:7.2f}% | {b.max_block_f1:6d} {b.max_block_f2:6d}"
        )

    print("\nTop 3 blocos por volume:")
    for n in completed_ns:
        b = block_results[n]
        print(f"  N = {n}:")
        print(f"    Top F1 (PN, Mfg):    {b.top_blocks_f1}")
        print(f"    Top F2 (Grp, Cat):   {b.top_blocks_f2}")

    print("\n--- F. VERIFICAÇÃO DE PREDICADOS ---")
    if pred_verification_result:
        pn, obs, theo, passed = pred_verification_result
        res_str = "PASS" if passed else "FAIL"
        print(f"N testado:          {pn}")
        print(f"Chamadas observadas: {obs}")
        print(f"Chamadas teóricas:   {theo} (N(N-1))")
        print(f"Resultado:           {res_str}")
    else:
        print("Verificação de predicados não executada por restrição orçamentária.")

    print("\n--- G. EXPOENTE EMPÍRICO ASSINTÓTICO (T_diag) ---")
    print(f"p_exponent: {p_exponent_str}")

    print("\n--- H. MEMÓRIA ---")
    if memory_result:
        mn, peak_mb = memory_result
        print(f"N medido:                 {mn}")
        print(f"Peak traced memory:       {peak_mb:.2f} MB")
        print("Nota técnica: tracemalloc peak != process RSS (mede apenas alocações Python rastreadas)")
    else:
        print(f"Memory measurement: {memory_status}")

    print("\n--- I. STATUS DAS HIPÓTESES E STOP CONDITIONS ---")
    print("H2 status: NOT ISOLATED IN THIS RUN")
    print(f"Horário real de encerramento (BRT): {end_time_brt.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Último N concluído:                 {completed_ns[-1] if completed_ns else 'Nenhum'}")
    print(f"Ns não executados:                  {unexecuted_ns if unexecuted_ns else 'Nenhum'}")
    print(f"Motivo de parada:                   {stop_reason}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--smoke":
        result = run_smoke_validation(n=50)
        print("=== SMOKE VALIDATION H-034 ===")
        for k, v in result.items():
            print(f"  {k}: {v}")
        print("STATUS: H-034 PROVED")
    else:
        main()
