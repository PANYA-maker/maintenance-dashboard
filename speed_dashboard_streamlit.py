// React + Tailwind + Recharts Interactive Dashboard
// NOTE: Replace SHEET_ID and ensure the Google Sheet is shared as Anyone with link → Viewer

import { useEffect, useMemo, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, BarChart, Bar, PieChart, Pie, Cell, ResponsiveContainer } from "recharts";

const SHEET_ID = "1Dd1PkTf2gW8tGSXVlr6WXgA974wcvySZTnVgv2G-7QU";
const SHEET_NAME = "DATA-SPEED";

function fetchSheet() {
  const url = `https://docs.google.com/spreadsheets/d/${SHEET_ID}/gviz/tq?tqx=out:json&sheet=${encodeURIComponent(SHEET_NAME)}`;
  return fetch(url)
    .then(r => r.text())
    .then(text => JSON.parse(text.substring(47).slice(0, -2)))
    .then(json => {
      const cols = json.table.cols.map(c => c.label);
      return json.table.rows.map(r => Object.fromEntries(r.c.map((v, i) => [cols[i], v ? v.v : null])));
    });
}

export default function Dashboard() {
  const [data, setData] = useState([]);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [machine, setMachine] = useState("all");
  const [shift, setShift] = useState("all");
  const [speedFlag, setSpeedFlag] = useState("all");
  const [stopType, setStopType] = useState("all");
  const [orderLen, setOrderLen] = useState("all");

  useEffect(() => {
    fetchSheet().then(setData);
  }, []);

  const filtered = useMemo(() => {
    return data.filter(d => {
      const dt = d.Date ? new Date(d.Date) : null;
      if (dateFrom && dt < new Date(dateFrom)) return false;
      if (dateTo && dt > new Date(dateTo)) return false;
      if (machine !== "all" && d.Machine !== machine) return false;
      if (shift !== "all" && d.Shift !== shift) return false;
      if (speedFlag !== "all" && d.Speed_vs_Plan !== speedFlag) return false;
      if (stopType !== "all" && d.Stop_Type !== stopType) return false;
      if (orderLen !== "all" && d.Order_Length !== orderLen) return false;
      return true;
    });
  }, [data, dateFrom, dateTo, machine, shift, speedFlag, stopType, orderLen]);

  const byDate = useMemo(() => {
    const m = {};
    filtered.forEach(d => {
      const k = d.Date;
      m[k] = m[k] || { Date: k, Actual: 0, Plan: 0 };
      m[k].Actual += Number(d.Speed_Actual || 0);
      m[k].Plan += Number(d.Speed_Plan || 0);
    });
    return Object.values(m);
  }, [filtered]);

  const stopPie = useMemo(() => {
    const m = {};
    filtered.forEach(d => { m[d.Stop_Type] = (m[d.Stop_Type] || 0) + 1; });
    return Object.entries(m).map(([name, value]) => ({ name, value }));
  }, [filtered]);

  const machines = ["all", ...new Set(data.map(d => d.Machine))].filter(Boolean);
  const shifts = ["all", ...new Set(data.map(d => d.Shift))].filter(Boolean);
  const speedFlags = ["all", ...new Set(data.map(d => d.Speed_vs_Plan))].filter(Boolean);
  const stopTypes = ["all", ...new Set(data.map(d => d.Stop_Type))].filter(Boolean);
  const orderLens = ["all", ...new Set(data.map(d => d.Order_Length))].filter(Boolean);

  return (
    <div className="p-6 grid gap-6">
      <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
        <Input type="date" value={dateFrom} onChange={e=>setDateFrom(e.target.value)} />
        <Input type="date" value={dateTo} onChange={e=>setDateTo(e.target.value)} />
        <Select value={machine} onValueChange={setMachine}><SelectTrigger><SelectValue placeholder="Machine"/></SelectTrigger><SelectContent>{machines.map(m=>(<SelectItem key={m} value={m}>{m}</SelectItem>))}</SelectContent></Select>
        <Select value={shift} onValueChange={setShift}><SelectTrigger><SelectValue placeholder="Shift"/></SelectTrigger><SelectContent>{shifts.map(s=>(<SelectItem key={s} value={s}>{s}</SelectItem>))}</SelectContent></Select>
        <Select value={speedFlag} onValueChange={setSpeedFlag}><SelectTrigger><SelectValue placeholder="Speed vs Plan"/></SelectTrigger><SelectContent>{speedFlags.map(s=>(<SelectItem key={s} value={s}>{s}</SelectItem>))}</SelectContent></Select>
        <Select value={stopType} onValueChange={setStopType}><SelectTrigger><SelectValue placeholder="Stop Type"/></SelectTrigger><SelectContent>{stopTypes.map(s=>(<SelectItem key={s} value={s}>{s}</SelectItem>))}</SelectContent></Select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card><CardContent className="h-72"><ResponsiveContainer><LineChart data={byDate}><XAxis dataKey="Date"/><YAxis/><Tooltip/><Legend/><Line dataKey="Actual"/><Line dataKey="Plan"/></LineChart></ResponsiveContainer></CardContent></Card>
        <Card><CardContent className="h-72"><ResponsiveContainer><PieChart><Pie data={stopPie} dataKey="value" nameKey="name" outerRadius={100}><Cell/><Cell/><Cell/><Cell/></Pie><Tooltip/></PieChart></ResponsiveContainer></CardContent></Card>
      </div>

      <Card>
        <CardContent>
          <div className="overflow-auto">
            <table className="min-w-full text-sm">
              <thead><tr>{Object.keys(filtered[0]||{}).map(k=>(<th key={k} className="px-2 py-1 text-left">{k}</th>))}</tr></thead>
              <tbody>{filtered.map((r,i)=>(<tr key={i} className="border-t">{Object.values(r).map((v,j)=>(<td key={j} className="px-2 py-1">{String(v)}</td>))}</tr>))}</tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
