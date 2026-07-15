"use client";

import { useCallback, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import {
  ArrowUpRight,
  Check,
  Command,
  Loader2,
  LockKeyhole,
  RefreshCw,
  Rss,
  X,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  generateBrief,
  getDashboard,
  getSources,
  updateAllSources,
  updateSource,
  type Asset,
  type DashboardData,
  type SourceDefinition,
} from "@/lib/api";

const emptyData: DashboardData = {
  today_brief: null,
  latest_ideas: [],
  recent_research: [],
  upcoming_tasks: [],
  stats: { total_assets: 0, ideas: 0, news: 0, research: 0, tasks: 0 },
};

const sourceGroups: Array<{ kind: SourceDefinition["kind"]; label: string }> = [
  { kind: "community", label: "社区讨论" },
  { kind: "official", label: "官方动态" },
  { kind: "code", label: "开源趋势" },
];

function formatToday() {
  return new Intl.DateTimeFormat("zh-CN", {
    weekday: "long",
    month: "long",
    day: "numeric",
  }).format(new Date());
}

function formatDate(date: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(date));
}

export function Dashboard() {
  const [data, setData] = useState<DashboardData>(emptyData);
  const [loading, setLoading] = useState(true);
  const [offline, setOffline] = useState(false);

  const load = useCallback(async () => {
    try {
      setData(await getDashboard());
      setOffline(false);
    } catch {
      setOffline(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <main className="min-h-screen bg-paper text-ink">
      <header className="border-b border-black/[0.07] bg-white/75 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-[1120px] items-center justify-between px-4 sm:px-7">
          <div className="flex items-center gap-2.5">
            <BrandMark />
            <span className="text-lg font-semibold">freja</span>
          </div>
          <p className="text-sm text-black/45">{formatToday()}</p>
        </div>
      </header>

      <div className="mx-auto max-w-[1120px] px-4 pb-20 pt-9 sm:px-7 sm:pt-12">
        <header className="mb-9 max-w-3xl">
          <p className="mb-3 text-sm font-semibold uppercase text-coral">Daily intelligence</p>
          <h1 className="text-3xl font-semibold sm:text-5xl">你的 AI 每日简报</h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-black/55 sm:text-lg">
            从你信任的来源中提取重要动态，整理成一份可追溯的中文摘要。
          </p>
        </header>

        {offline && <OfflineNotice />}

        <WorkflowSteps hasBrief={Boolean(data.today_brief)} />
        <SourceWorkspace brief={data.today_brief} onBriefUpdated={load} />
        <BriefPanel brief={data.today_brief} loading={loading} />
      </div>
    </main>
  );
}

function BrandMark() {
  return (
    <div className="grid h-8 w-8 place-items-center rounded-md bg-coral text-white">
      <Command className="h-[18px] w-[18px]" />
    </div>
  );
}

function OfflineNotice() {
  return (
    <div className="mb-6 flex items-center gap-3 rounded-md border border-gold/30 bg-gold/10 px-4 py-3 text-sm">
      <span className="h-2 w-2 rounded-full bg-gold" />
      <span>Freja API 暂时无法连接。</span>
    </div>
  );
}

function WorkflowSteps({ hasBrief }: { hasBrief: boolean }) {
  const steps = ["选择来源", "采集与排序", "阅读摘要", "打开原文"];
  return (
    <ol className="mb-6 grid grid-cols-2 border-y border-black/[0.07] sm:grid-cols-4" aria-label="简报流程">
      {steps.map((step, index) => (
        <li key={step} className="flex min-h-14 items-center gap-3 border-black/[0.07] py-3 pr-3 sm:border-r sm:px-4 sm:first:pl-0 sm:last:border-r-0">
          <span className={`grid h-6 w-6 shrink-0 place-items-center rounded-full text-xs font-semibold ${hasBrief && index > 1 ? "bg-moss text-white" : index === 0 ? "bg-coral text-white" : "bg-black/[0.06] text-black/45"}`}>
            {hasBrief && index > 1 ? <Check className="h-3.5 w-3.5" /> : index + 1}
          </span>
          <span className="text-sm font-medium text-black/60">{step}</span>
        </li>
      ))}
    </ol>
  );
}

function SourceWorkspace({ brief, onBriefUpdated }: { brief: Asset | null; onBriefUpdated: () => Promise<void> }) {
  const [sources, setSources] = useState<SourceDefinition[]>([]);
  const [loading, setLoading] = useState(true);
  const [dirty, setDirty] = useState(false);
  const [updating, setUpdating] = useState<string | null>(null);
  const [bulkUpdating, setBulkUpdating] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getSources()
      .then(setSources)
      .catch((reason) => setError(reason instanceof Error ? reason.message : "无法读取来源"))
      .finally(() => setLoading(false));
  }, []);

  const visibleSources = sources.filter((source) => source.availability !== "planned");
  const availableSources = visibleSources.filter((source) => source.availability === "available");
  const enabledCount = visibleSources.filter((source) => source.enabled).length;
  const allSelected = availableSources.length > 0 && availableSources.every((source) => source.enabled);

  async function toggle(source: SourceDefinition) {
    setUpdating(source.id);
    setError(null);
    try {
      setSources(await updateSource(source.id, !source.enabled));
      setDirty(true);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "无法更新来源");
    } finally {
      setUpdating(null);
    }
  }

  async function setAll(enabled: boolean) {
    setBulkUpdating(true);
    setError(null);
    try {
      setSources(await updateAllSources(enabled));
      setDirty(true);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "无法更新来源");
    } finally {
      setBulkUpdating(false);
    }
  }

  async function buildBrief() {
    setGenerating(true);
    setError(null);
    try {
      const previousBriefId = brief?.id ?? null;
      await generateBrief();
      const deadline = Date.now() + 120_000;
      while (Date.now() < deadline) {
        await new Promise((resolve) => window.setTimeout(resolve, 3000));
        const dashboard = await getDashboard();
        if (dashboard.today_brief?.id && dashboard.today_brief.id !== previousBriefId) {
          await onBriefUpdated();
          setDirty(false);
          document.getElementById("today-brief")?.scrollIntoView({ behavior: "smooth", block: "start" });
          return;
        }
      }
      throw new Error("生成仍在进行，请稍后再试。");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "简报生成失败");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <section className="mb-10 rounded-md border border-black/[0.08] bg-white" aria-labelledby="source-heading">
      <div className="flex flex-col gap-4 border-b border-black/[0.07] px-5 py-5 sm:flex-row sm:items-center sm:justify-between sm:px-7">
        <div>
          <div className="flex items-center gap-2">
            <Rss className="h-4 w-4 text-coral" />
            <h2 id="source-heading" className="text-lg font-semibold">选择来源</h2>
          </div>
          <p className="mt-1 text-sm text-black/45">已选择 {enabledCount} 个来源</p>
        </div>
        <div className="flex items-center gap-1">
          <Button size="sm" variant="ghost" onClick={() => setAll(true)} disabled={loading || bulkUpdating || allSelected}>
            {bulkUpdating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
            全选
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setAll(false)} disabled={loading || bulkUpdating || enabledCount === 0}>
            <X className="h-4 w-4" />
            全不选
          </Button>
        </div>
      </div>

      <div className="px-5 py-2 sm:px-7">
        {loading ? (
          <div className="grid min-h-44 place-items-center"><Loader2 className="h-6 w-6 animate-spin text-black/30" /></div>
        ) : sourceGroups.map((group) => {
          const groupSources = visibleSources.filter((source) => source.kind === group.kind);
          if (!groupSources.length) return null;
          return (
            <fieldset key={group.kind} className="border-b border-black/[0.06] py-5 last:border-b-0">
              <legend className="mb-3 text-xs font-semibold uppercase text-black/35">{group.label}</legend>
              <div className="grid gap-x-7 gap-y-2 sm:grid-cols-2">
                {groupSources.map((source) => {
                  const unavailable = source.availability !== "available";
                  const disabled = unavailable || updating === source.id || bulkUpdating || generating;
                  return (
                    <label key={source.id} className={`flex min-h-14 items-center gap-3 rounded-md px-3 py-2 transition-colors ${disabled ? "cursor-not-allowed text-black/30" : "cursor-pointer hover:bg-black/[0.025]"}`}>
                      <input
                        type="checkbox"
                        checked={source.enabled}
                        disabled={disabled}
                        onChange={() => toggle(source)}
                        className="h-[18px] w-[18px] shrink-0 accent-coral"
                        aria-label={`Include ${source.name}`}
                      />
                      <span className="min-w-0 flex-1">
                        <span className="flex items-center gap-2 text-sm font-semibold">
                          {source.name}
                          {source.health === "healthy" && <span className="h-1.5 w-1.5 rounded-full bg-moss" title="Healthy" />}
                        </span>
                        <span className="mt-0.5 block truncate text-xs text-black/35">{source.acquisition}</span>
                      </span>
                      {updating === source.id ? <Loader2 className="h-4 w-4 animate-spin" /> : unavailable ? <LockKeyhole className="h-4 w-4" /> : null}
                    </label>
                  );
                })}
              </div>
            </fieldset>
          );
        })}
      </div>

      {error && <p className="mx-5 mb-4 rounded-md bg-coral/10 px-4 py-3 text-sm text-coral sm:mx-7">{error}</p>}

      <div className="flex flex-col gap-4 border-t border-black/[0.07] bg-[#fbfaf7] px-5 py-5 sm:flex-row sm:items-center sm:justify-between sm:px-7">
        <div className="min-h-10">
          {generating ? (
            <div className="flex items-center gap-3 text-sm text-black/55">
              <Loader2 className="h-4 w-4 animate-spin text-coral" />
              正在采集、排序并撰写中文摘要…
            </div>
          ) : (
            <p className="text-sm text-black/45">
              {dirty ? "来源已更新，生成后会应用新选择。" : brief ? `上次生成于 ${formatDate(brief.created_at)}` : "准备生成第一份简报。"}
            </p>
          )}
        </div>
        <Button variant="coral" onClick={buildBrief} disabled={loading || generating || bulkUpdating || enabledCount === 0} className="w-full sm:w-auto">
          {generating ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          {generating ? "正在生成" : brief ? "重新生成简报" : "生成简报"}
        </Button>
      </div>
    </section>
  );
}

function BriefPanel({ brief, loading }: { brief: Asset | null; loading: boolean }) {
  const itemCount = typeof brief?.metadata.item_ids === "object" && Array.isArray(brief.metadata.item_ids)
    ? brief.metadata.item_ids.length
    : null;

  return (
    <section id="today-brief" className="scroll-mt-6" aria-labelledby="brief-heading">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="mb-1 text-xs font-semibold uppercase text-coral">Your brief</p>
          <h2 id="brief-heading" className="text-2xl font-semibold">今日简报</h2>
        </div>
        {brief && <p className="text-sm text-black/40">{formatDate(brief.created_at)}{itemCount ? ` · ${itemCount} 条信号` : ""}</p>}
      </div>

      <div className="min-h-[360px] rounded-md border border-black/[0.08] bg-white">
        {loading ? (
          <div className="grid min-h-[360px] place-items-center"><Loader2 className="h-6 w-6 animate-spin text-black/30" /></div>
        ) : brief ? (
          <div className="px-5 py-7 sm:px-10 sm:py-10">
            <div className="mb-7 flex items-center gap-2 border-b border-black/[0.07] pb-5">
              <Badge className="bg-coral/10 text-coral">AI Brief</Badge>
              <span className="text-xs text-black/35">中文摘要 · 来源可追溯</span>
            </div>
            <article className="brief-markdown mx-auto max-w-[780px]">
              <ReactMarkdown
                components={{
                  a: ({ children, node: _node, ...props }) => (
                    <a {...props} target="_blank" rel="noopener noreferrer">
                      {children}<ArrowUpRight className="ml-1 inline h-3.5 w-3.5" aria-hidden="true" />
                    </a>
                  ),
                }}
              >
                {brief.content}
              </ReactMarkdown>
            </article>
          </div>
        ) : (
          <div className="grid min-h-[360px] place-items-center px-6 text-center">
            <div className="max-w-md">
              <div className="mx-auto mb-5 grid h-11 w-11 place-items-center rounded-md bg-coral/10 text-coral"><Rss className="h-5 w-5" /></div>
              <h3 className="text-xl font-semibold">还没有简报</h3>
              <p className="mt-2 text-sm leading-6 text-black/45">选择上方来源并生成，简报会显示在这里。</p>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
