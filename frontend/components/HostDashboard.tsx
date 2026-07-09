"use client";

import { useEffect, useState } from "react";

type Approval = {
  id: string;
  booking_id: string;
  guest_message: string;
  change: Record<string, unknown>;
  status: string;
};
type Escalation = { id: string; guest_id: string; reason: string };

function formatChange(change: Record<string, unknown>): string {
  return Object.entries(change)
    .map(([key, value]) => `${key}: ${value}`)
    .join(", ");
}

export function HostDashboard() {
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [escalations, setEscalations] = useState<Escalation[]>([]);

  useEffect(() => {
    fetch("/api/host/approvals")
      .then((response) => response.json())
      .then(setApprovals);
    fetch("/api/host/escalations")
      .then((response) => response.json())
      .then(setEscalations);
  }, []);

  async function decide(approvalId: string, decision: "approve" | "deny") {
    await fetch("/api/host/decision", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ approval_id: approvalId, decision }),
    });
    setApprovals((prev) => prev.filter((approval) => approval.id !== approvalId));
  }

  return (
    <div>
      <section>
        <h2>Approvals</h2>
        <ul>
          {approvals.map((approval) => (
            <li key={approval.id}>
              <p>{approval.booking_id}</p>
              <p>Guest asked: &ldquo;{approval.guest_message}&rdquo;</p>
              <p>Proposed change: {formatChange(approval.change)}</p>
              <button onClick={() => decide(approval.id, "approve")}>Approve</button>
              <button onClick={() => decide(approval.id, "deny")}>Deny</button>
            </li>
          ))}
        </ul>
      </section>
      <section>
        <h2>Escalations</h2>
        <ul>
          {escalations.map((escalation) => (
            <li key={escalation.id}>{escalation.reason}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}
