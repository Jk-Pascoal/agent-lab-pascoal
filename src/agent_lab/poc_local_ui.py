"""Local, dependency-free browser journey for synthetic/authorized CSV PoC (#210).

python -m agent_lab.poc_local_ui [--port 8765]
Binds only to loopback. No ERP, external network, human decisions or production claims.
"""
import argparse
import csv
import json
import secrets
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from urllib.parse import parse_qs, urlsplit

from .catalog_csv_adapter import load_catalog_materials
from .catalog_quality_use_case import DiagnoseCatalogQualityUseCase
from .poc_audit_report import write_poc_audit_report
from .poc_audit_triage import verified_triage_csv
from .poc_audit_verify import InvalidPocAuditPairError, verify_poc_audit_report_pair

MAX_CSV_BYTES = 256 * 1024
MAX_MATERIALS = 200
MAX_SESSIONS = 10

PAGE = r'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agent Lab Pascoal · Triagem local</title>
<style>
:root{font-family:system-ui,Arial,sans-serif;color-scheme:dark;background:#0b1217;color:#e7edf0}
*{box-sizing:border-box}body{margin:0}main{max-width:1100px;margin:32px auto;padding:0 20px}
header{border-bottom:1px solid #34434a;padding-bottom:25px}
small,.muted{color:#a9bac3}h1{font-size:clamp(25px,4vw,40px)}
.tag{color:#5bdae1;font-size:12px;letter-spacing:.12em;text-transform:uppercase}
.panel{border:1px solid #30434a;border-radius:12px;padding:20px;margin:20px 0;background:#122029}
label{display:block;margin:8px 0;font-weight:600}input,button,select{font:inherit;padding:11px;border-radius:7px}
input[type=file],input[type=text],select{width:100%;color:inherit;border:1px solid #45616b;background:#0b171f}
.row{display:grid;grid-template-columns:2fr 1fr;gap:16px}
button{margin-top:15px;border:0;background:#25b8c1;color:#092024;font-weight:700;cursor:pointer}
button:disabled{opacity:.5}a{color:#7cdee5}
.metrics,.downloads{display:flex;flex-wrap:wrap;gap:12px}
.metric{border:1px solid #38505b;border-radius:8px;padding:14px;min-width:140px;flex:1}
.metric strong{font-size:24px;display:block}table{border-collapse:collapse;width:100%;font-size:14px}
th,td{padding:11px;border-bottom:1px solid #334650;text-align:left;vertical-align:top;overflow-wrap:anywhere}
th{color:#9ed4d7}details{max-width:420px}summary{cursor:pointer;color:#aee3e4}
#error{color:#ffaaaa}@media(max-width:700px){.row{grid-template-columns:1fr}.table-scroll{overflow-x:auto}}
</style></head><body><main>
<header><div class="tag">Agent Lab Pascoal · PoC sintética</div>
<h1>Diagnóstico e triagem de materiais</h1>
<p class="muted">CSV → diagnóstico real → relatório JSON verificado → triagem e exportação.</p>
<small>Somente CSV sintético ou autorizado. Sem ERP, decisão humana ou custódia física comprovada.</small></header>
<section class="panel"><h2>1. Importar catálogo</h2>
<div class="row"><div><label for="csv">Arquivo CSV (até 256 KiB e 200 materiais)</label>
<input id="csv" type="file" accept=".csv,text/csv"></div>
<div><label for="catalog">Identificador do catálogo</label>
<input id="catalog" type="text" maxlength="70" value="POC-210-LOCAL"></div></div>
<button id="analyze">Executar diagnóstico verificado</button>
<p id="status" role="status"></p><p id="error" role="alert"></p></section>
<section class="panel" id="result" hidden><h2>2. Resultado verificado</h2>
<p class="muted">Recomendações automáticas ≠ decisões humanas. Proveniência: UNAVAILABLE; HumanReview: NOT_RECORDED.</p>
<div id="metrics" class="metrics"></div><h2>3. Inspecionar recomendações</h2>
<label for="filter">Filtrar registros</label><select id="filter">
<option value="ALL">Todos</option><option value="ACTIONABLE">Somente REVIEW / REJECT</option>
<option value="REVIEW">REVIEW</option><option value="REJECT">REJECT</option>
<option value="APPROVE">APPROVE (algoritmo)</option></select>
<p id="count" class="muted"></p><div class="table-scroll"><table>
<thead><tr><th>Material</th><th>Recomendação</th><th>Completude</th>
<th>Problemas e evidências</th></tr></thead><tbody id="records"></tbody>
</table></div><h2>4. Baixar evidências</h2>
<div id="downloads" class="downloads"></div>
<p class="muted">O manifesto atesta os bytes do relatório, não a origem do CSV nem atomicidade em power-loss.</p>
</section><footer><small>Experimento local · Issue #210 · sem transmissão externa.</small></footer></main>
<script>
'use strict';
const TOKEN=__TOKEN__;
const file=document.getElementById('csv');
const button=document.getElementById('analyze');
const status=document.getElementById('status');
const error=document.getElementById('error');
const result=document.getElementById('result');
const records=document.getElementById('records');
const filter=document.getElementById('filter');
let rows=[];
function cell(tr,value){const td=document.createElement('td');td.textContent=String(value);tr.appendChild(td);return td;}
function redraw(){
 records.replaceChildren();
 const f=filter.value;
 const shown=rows.filter(r=>f==='ALL'||(f==='ACTIONABLE'&&['REVIEW','REJECT'].includes(r.recommendation))||r.recommendation===f);
 document.getElementById('count').textContent=shown.length+' de '+rows.length+' registros';
 for(const r of shown){
  const tr=document.createElement('tr');cell(tr,r.material_id);cell(tr,r.recommendation+' (automática)');
  cell(tr,(100*r.completeness).toFixed(1)+'%');
  const td=cell(tr,r.issues.length+' problema(s), '+r.duplicate_candidates.length+' candidato(s)');
  const details=document.createElement('details'),heading=document.createElement('summary');
  heading.textContent='Inspecionar evidências';details.appendChild(heading);
  const pre=document.createElement('pre');pre.style.whiteSpace='pre-wrap';
  pre.textContent=JSON.stringify({issues:r.issues,evidence:r.evidence,duplicate_candidates:r.duplicate_candidates,
    source_row_status:r.source_row_status,human_review:r.human_review},null,2);
  details.appendChild(pre);td.appendChild(details);records.appendChild(tr);
 }
}
filter.addEventListener('change',redraw);
button.addEventListener('click',async()=>{
 error.textContent='';status.textContent='';result.hidden=true;rows=[];
 if(!file.files.length){error.textContent='Selecione um CSV.';return;}
 const f=file.files[0];
 if(f.size===0||f.size>262144){error.textContent='CSV vazio ou maior que 256 KiB.';return;}
 button.disabled=true;status.textContent='Analisando localmente…';
 try{
  const response=await fetch('/analyze?catalog_id='+encodeURIComponent(document.getElementById('catalog').value),
    {method:'POST',headers:{'Content-Type':'text/csv','X-Poc-Token':TOKEN},body:await f.arrayBuffer()});
  const data=await response.json();if(!response.ok)throw new Error(data.error||'Análise recusada');
  rows=data.records;const metrics=document.getElementById('metrics');metrics.replaceChildren();
  for(const [label,n] of [['Registros',data.summary.total_records],
    ['Com problemas bloqueantes',data.summary.records_with_blocking_issues_count],
    ['Pares candidatos',data.summary.duplicate_pairs_count],['Problemas',data.summary.total_issues_count]]){
    const card=document.createElement('div');card.className='metric';
    const number=document.createElement('strong');number.textContent=String(n);
    card.append(number,document.createTextNode(label));metrics.appendChild(card);
  }
  const dl=document.getElementById('downloads');dl.replaceChildren();
  for(const [name,url] of Object.entries(data.downloads)){
    const a=document.createElement('a');a.href=url;
    a.textContent=({report:'Relatório JSON',manifest:'Manifesto SHA-256',triage:'Triagem CSV'})[name];
    dl.appendChild(a);
  }
  filter.value='ALL';redraw();result.hidden=false;
  status.textContent='Par relatório/manifesto verificado antes da apresentação.';
 }catch(e){error.textContent='Recusado: '+e.message;status.textContent='Nenhum resultado parcial exibido.';}
 finally{button.disabled=false;}
});
</script></body></html>'''


def run_diagnostic(csv_bytes: bytes, catalog_id: str, directory: Path) -> tuple[Path, dict]:
    """Use the real #204 adapter, use case, exporter and fail-closed consumers."""
    if not 0 < len(csv_bytes) <= MAX_CSV_BYTES:
        raise ValueError("invalid CSV size")
    if not catalog_id or not catalog_id.strip() or len(catalog_id) > 70:
        raise ValueError("invalid catalog identifier")
    source = directory / "input.csv"
    source.write_bytes(csv_bytes)
    catalog = load_catalog_materials(source)
    if not catalog:
        raise ValueError("empty catalog")
    if len(catalog) > MAX_MATERIALS:
        raise ValueError("experimental limit of 200 materials")
    report = DiagnoseCatalogQualityUseCase().execute(catalog, catalog_id=catalog_id)
    path = directory / "report.json"
    write_poc_audit_report(report, path)
    verified = verify_poc_audit_report_pair(path)
    verified_triage_csv(path)
    return path, verified


class LocalPocServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, port: int):
        self.workspace = tempfile.TemporaryDirectory(prefix="agentlab-poc210-")
        self.csrf_token = secrets.token_urlsafe(32)
        self.runs: dict[str, Path] = {}
        self.run_lock = Lock()
        try:
            super().__init__(("127.0.0.1", port), LocalPocHandler)
        except Exception:
            self.workspace.cleanup()
            raise

    def server_close(self):
        super().server_close()
        self.workspace.cleanup()


class LocalPocHandler(BaseHTTPRequestHandler):
    server: LocalPocServer

    def _send(self, status: int, data: bytes, kind: str, *, filename: str | None = None):
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy",
            "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
            "connect-src 'self'; base-uri 'none'; form-action 'none'")
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(data)

    def _json(self, status: int, value: dict):
        self._send(status, json.dumps(value, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def _trusted_host(self):
        return self.headers.get("Host") in {
            f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"
        }

    def do_GET(self):
        if not self._trusted_host():
            return self._json(403, {"error": "Host recusado"})
        route = urlsplit(self.path).path
        if route == "/":
            html = PAGE.replace("__TOKEN__", json.dumps(self.server.csrf_token)).encode("utf-8")
            return self._send(200, html, "text/html; charset=utf-8")
        segments = route.split("/")
        if len(segments) != 4 or segments[1] != "artifact" or segments[3] not in ("report", "manifest", "triage"):
            return self._json(404, {"error": "Rota inexistente"})
        with self.server.run_lock:
            path = self.server.runs.get(segments[2])
        if path is None:
            return self._json(404, {"error": "Execução inexistente"})
        try:
            verify_poc_audit_report_pair(path)
            if segments[3] == "report":
                data, kind, filename = path.read_bytes(), "application/json", "report.json"
            elif segments[3] == "manifest":
                data, kind, filename = path.with_name("report.json.manifest.json").read_bytes(), "application/json", "report.json.manifest.json"
            else:
                data, kind, filename = verified_triage_csv(path).encode("utf-8"), "text/csv; charset=utf-8", "triage.csv"
        except (OSError, InvalidPocAuditPairError):
            return self._json(409, {"error": "Par relatório/manifesto não verificado"})
        self._send(200, data, kind, filename=filename)

    def do_POST(self):
        if not self._trusted_host():
            return self._json(403, {"error": "Host recusado"})
        if urlsplit(self.path).path != "/analyze":
            return self._json(404, {"error": "Rota inexistente"})
        origin = self.headers.get("Origin")
        allowed = {f"http://127.0.0.1:{self.server.server_port}",
                   f"http://localhost:{self.server.server_port}"}
        if (origin is not None and origin not in allowed or
            self.headers.get("X-Poc-Token") != self.server.csrf_token or
            self.headers.get("Content-Type", "").split(";")[0] != "text/csv"):
            return self._json(403, {"error": "Requisição local não autorizada"})
        try:
            count = int(self.headers.get("Content-Length", ""))
        except ValueError:
            return self._json(411, {"error": "Content-Length obrigatório"})
        if not 0 < count <= MAX_CSV_BYTES:
            return self._json(413, {"error": "CSV vazio ou maior que 256 KiB"})
        data = self.rfile.read(count)
        if len(data) != count:
            return self._json(400, {"error": "CSV incompleto"})
        catalog_id = parse_qs(urlsplit(self.path).query).get("catalog_id", ["POC-210-LOCAL"])[0]
        with self.server.run_lock:
            if len(self.server.runs) >= MAX_SESSIONS:
                return self._json(429, {"error": "Limite de sessões; reinicie a interface"})
            run_id = secrets.token_urlsafe(18)
            directory = Path(self.server.workspace.name) / run_id
            directory.mkdir()
            self.server.runs[run_id] = directory / "report.json"
        try:
            _, verified = run_diagnostic(data, catalog_id, directory)
        except (ValueError, TypeError, OSError, UnicodeError, csv.Error) as exc:
            with self.server.run_lock:
                self.server.runs.pop(run_id, None)
            return self._json(422, {"error": f"Entrada recusada: {type(exc).__name__}"})
        except Exception:
            with self.server.run_lock:
                self.server.runs.pop(run_id, None)
            self.log_error("unexpected pipeline failure")
            return self._json(500, {"error": "Falha interna; nenhum resultado publicado"})
        prefix = f"/artifact/{run_id}/"
        self._json(200, {
            "summary": verified["summary"], "records": verified["records"],
            "downloads": {k: prefix+k for k in ("report", "manifest", "triage")},
            "source_custody": "UNAVAILABLE", "human_review": "NOT_RECORDED",
        })

    def log_message(self, format, *args):
        # Do not log input rows or catalog identity.
        pass


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    with LocalPocServer(args.port) as server:
        print(f"Agent Lab PoC local: http://127.0.0.1:{server.server_port}/", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor encerrado; arquivos temporários descartados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
