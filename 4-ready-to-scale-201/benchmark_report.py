import yaml
from pathlib import Path


def generate_html_report(yaml_path, html_path):
    """Generate an HTML benchmark report from a GuideLLM YAML results file."""
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    b = data["benchmarks"][0]
    m = b["metrics"]
    totals = b["request_totals"]
    worker = b["worker"]
    reqs = b["requests"]["successful"]

    # Helper to get a stat
    def s(metric, field, category="successful"):
        return m[metric][category][field]

    # Build per-request table rows and chart bars
    max_tok = max(r["output_tokens"] for r in reqs)
    max_lat = max(r["request_latency"] for r in reqs)
    req_rows = ""
    tok_bars = ""
    lat_bars = ""
    for i, r in enumerate(reqs):
        req_rows += (
            f'<tr><td>{i+1}</td>'
            f'<td class="n">{r["prompt_tokens"]}</td>'
            f'<td class="n">{r["output_tokens"]}</td>'
            f'<td class="n">{r["request_latency"]:.2f}</td>'
            f'<td class="n">{r["time_to_first_token_ms"]:.1f}</td>'
            f'<td class="n">{r["inter_token_latency_ms"]:.2f}</td>'
            f'<td class="n">{r["output_tokens_per_second"]:.1f}</td>'
            f'<td class="n">{r["time_per_output_token_ms"]:.2f}</td></tr>\n'
        )
        tok_bars += f'<div class="bar" style="height:{r["output_tokens"]/max_tok*100:.0f}%"><div class="tip">Req {i+1}: {r["output_tokens"]} tok</div></div>\n'
        lat_bars += f'<div class="bar b2" style="height:{r["request_latency"]/max_lat*100:.0f}%"><div class="tip">Req {i+1}: {r["request_latency"]:.2f}s</div></div>\n'

    # Percentile bar helper
    def pbar(metric, pct, max_val, unit=""):
        val = s(metric, "percentiles")[pct]
        w = val / max_val * 100 if max_val else 0
        return f'<div class="pb"><span class="pl">{pct}</span><div class="bg"><div class="f" style="width:{w:.0f}%"></div></div><span class="pv">{val:.2f}{unit}</span></div>'

    # Build percentile sections
    def percentile_section(title, metric, unit, max_val=None):
        if max_val is None:
            max_val = s(metric, "max")
        return f"""<div class="cd">
<h3 class="sh">{title}</h3>
{pbar(metric, "p50", max_val, unit)}
{pbar(metric, "p90", max_val, unit)}
{pbar(metric, "p95", max_val, unit)}
{pbar(metric, "p99", max_val, unit)}
<div class="sm">Min: {s(metric,"min"):.2f} | Max: {s(metric,"max"):.2f} | Std: {s(metric,"std_dev"):.2f}</div>
</div>"""

    success_pct = totals["successful"] / totals["total"] * 100 if totals["total"] else 0
    strategy = b["args"]["strategy"]["type_"].title()
    processor = b["request_loader"]["processor"]

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Benchmark Report - {worker["backend_model"]}</title>
<style>
:root{{--bg:#0f1117;--c:#1a1d27;--bd:#2a2d3a;--t:#e4e4e7;--m:#9ca3af;--a:#6366f1;--a2:#8b5cf6;--g:#22c55e;--y:#eab308;--r:#ef4444;--bl:#3b82f6;--cy:#06b6d4}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:system-ui,sans-serif;background:var(--bg);color:var(--t);line-height:1.6}}
.w{{max-width:1280px;margin:0 auto;padding:24px}}
h1{{font-size:28px;text-align:center;padding:40px 0 8px;background:linear-gradient(135deg,var(--a),var(--a2));-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.st{{text-align:center;color:var(--m);font-size:14px;margin-bottom:32px}}
.bdg{{display:inline-block;background:var(--c);border:1px solid var(--bd);border-radius:6px;padding:6px 16px;font-size:13px;color:var(--cy)}}
h2{{font-size:18px;font-weight:600;margin:32px 0 16px;padding-bottom:8px;border-bottom:1px solid var(--bd)}}
.g4{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:16px}}
.g2{{display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:16px;margin-bottom:16px}}
.cd{{background:var(--c);border:1px solid var(--bd);border-radius:10px;padding:20px}}
.cd .l{{font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--m);margin-bottom:4px}}
.cd .v{{font-size:28px;font-weight:700}}.cd .u{{font-size:14px;color:var(--m);font-weight:400}}.cd .ss{{font-size:12px;color:var(--m);margin-top:4px}}
.sc{{text-align:center}}.sc .ct{{font-size:32px;font-weight:700}}
.sc.ok .ct{{color:var(--g)}}.sc.er .ct{{color:var(--r)}}.sc.ic .ct{{color:var(--y)}}.sc.to .ct{{color:var(--bl)}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{text-align:left;padding:10px 12px;background:rgba(99,102,241,.1);color:var(--a);font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.05em}}
td{{padding:10px 12px;border-bottom:1px solid var(--bd)}}.n{{text-align:right;font-variant-numeric:tabular-nums}}
.sh{{font-size:14px;margin-bottom:16px;color:var(--m)}}
.sm{{margin-top:12px;font-size:12px;color:var(--m)}}
.pb{{display:flex;align-items:center;gap:8px;margin-bottom:6px}}.pl{{width:36px;font-size:12px;color:var(--m);text-align:right}}
.bg{{flex:1;height:20px;background:rgba(99,102,241,.1);border-radius:4px;overflow:hidden}}.f{{height:100%;border-radius:4px;background:linear-gradient(90deg,var(--a),var(--a2))}}
.pv{{width:80px;font-size:12px;text-align:right;font-variant-numeric:tabular-nums}}
.ch{{position:relative;height:200px;margin:16px 0}}.bc{{display:flex;align-items:flex-end;gap:4px;height:100%;padding:0 8px}}
.bar{{flex:1;background:linear-gradient(180deg,var(--a),var(--a2));border-radius:3px 3px 0 0;min-width:16px;position:relative}}
.b2{{background:linear-gradient(180deg,var(--cy),var(--bl))}}
.bar:hover .tip{{display:block}}.tip{{display:none;position:absolute;bottom:100%;left:50%;transform:translateX(-50%);background:var(--c);border:1px solid var(--bd);padding:4px 8px;border-radius:4px;font-size:11px;white-space:nowrap;z-index:10}}
.ir{{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--bd);font-size:13px}}.ir:last-child{{border-bottom:none}}.il{{color:var(--m)}}
.bg2{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;background:rgba(34,197,94,.15);color:var(--g)}}
footer{{text-align:center;padding:32px 0;color:var(--m);font-size:12px;border-top:1px solid var(--bd);margin-top:40px}}
</style></head>
<body><div class="w">

<h1>GuideLLM Benchmark Report</h1>
<div class="st">Generative Benchmark Performance Analysis<br><span class="bdg">{worker["backend_model"]} &mdash; {worker["backend_target"]}</span></div>

<h2>Run Overview</h2>
<div class="g4">
<div class="cd"><div class="l">Duration</div><div class="v">{b["duration"]:.1f}<span class="u">s</span></div></div>
<div class="cd"><div class="l">Strategy</div><div class="v" style="font-size:20px">{strategy}</div><div class="ss">Concurrency: ~{s("request_concurrency","mean"):.1f}</div></div>
<div class="cd"><div class="l">Processor</div><div class="v" style="font-size:13px;word-break:break-all">{processor}</div></div>
</div>

<h2>Request Summary</h2>
<div class="g4">
<div class="cd sc to"><div class="l">Total</div><div class="ct">{totals["total"]}</div></div>
<div class="cd sc ok"><div class="l">Successful</div><div class="ct">{totals["successful"]}</div><div class="ss">{success_pct:.1f}%</div></div>
<div class="cd sc ic"><div class="l">Incomplete</div><div class="ct">{totals["incomplete"]}</div></div>
<div class="cd sc er"><div class="l">Errored</div><div class="ct">{totals["errored"]}</div></div>
</div>

<h2>Key Performance Metrics (Successful)</h2>
<div class="g4">
<div class="cd"><div class="l">Requests/Second</div><div class="v">{s("requests_per_second","mean"):.3f}<span class="u"> req/s</span></div></div>
<div class="cd"><div class="l">Output Tokens/Sec</div><div class="v">{s("output_tokens_per_second","mean"):.1f}<span class="u"> tok/s</span></div></div>
<div class="cd"><div class="l">Time to First Token</div><div class="v">{s("time_to_first_token_ms","mean"):.0f}<span class="u"> ms</span></div></div>
<div class="cd"><div class="l">Request Latency</div><div class="v">{s("request_latency","mean"):.2f}<span class="u"> s</span></div></div>
</div>
<div class="g4">
<div class="cd"><div class="l">Inter-Token Latency</div><div class="v">{s("inter_token_latency_ms","mean"):.1f}<span class="u"> ms</span></div></div>
<div class="cd"><div class="l">Time/Output Token</div><div class="v">{s("time_per_output_token_ms","mean"):.1f}<span class="u"> ms</span></div></div>
<div class="cd"><div class="l">Avg Prompt Tokens</div><div class="v">{s("prompt_token_count","mean"):.0f}<span class="u"> tok</span></div></div>
<div class="cd"><div class="l">Avg Output Tokens</div><div class="v">{s("output_token_count","mean"):.0f}<span class="u"> tok</span></div></div>
</div>

<h2>Latency Distributions (Successful)</h2>
<div class="g2">
{percentile_section("Request Latency (s)", "request_latency", "s")}
{percentile_section("Time to First Token (ms)", "time_to_first_token_ms", "ms")}
</div>
<div class="g2">
{percentile_section("Inter-Token Latency (ms)", "inter_token_latency_ms", "ms")}
{percentile_section("Output Tokens/Second", "output_tokens_per_second", "")}
</div>

<h2>Output Tokens per Request</h2>
<div class="cd"><div class="ch"><div class="bc">{tok_bars}</div></div>
<div style="text-align:center;font-size:12px;color:var(--m)">Request Index</div></div>

<h2>Request Latency per Request</h2>
<div class="cd"><div class="ch"><div class="bc">{lat_bars}</div></div>
<div style="text-align:center;font-size:12px;color:var(--m)">Request Index</div></div>

<h2>Per-Request Details</h2>
<div class="cd" style="overflow-x:auto">
<table><thead><tr>
<th>#</th><th class="n">Prompt Tok</th><th class="n">Output Tok</th><th class="n">Latency (s)</th>
<th class="n">TTFT (ms)</th><th class="n">ITL (ms)</th><th class="n">Out tok/s</th><th class="n">TPOT (ms)</th>
</tr></thead><tbody>{req_rows}</tbody></table></div>

<h2>Backend Configuration</h2>
<div class="cd">
<div class="ir"><span class="il">Backend Type</span><span>{worker["backend_type"]}</span></div>
<div class="ir"><span class="il">Model</span><span>{worker["backend_model"]}</span></div>
<div class="ir"><span class="il">Target URL</span><span>{worker["backend_target"]}</span></div>
<div class="ir"><span class="il">Max Output Tokens</span><span>{worker["backend_info"]["max_output_tokens"]:,}</span></div>
<div class="ir"><span class="il">Timeout</span><span>{worker["backend_info"]["timeout"]}s</span></div>
<div class="ir"><span class="il">HTTP/2</span><span><span class="bg2">{"Enabled" if worker["backend_info"]["http2"] else "Disabled"}</span></span></div>
</div>

<footer>Generated from GuideLLM benchmark data &bull; Benchmark ID: {b["id_"]}</footer>
</div></body></html>"""

    Path(html_path).write_text(html)
    print(f"HTML report saved to: {html_path}")
