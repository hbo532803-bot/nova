import { useEffect, useState } from "react";
import MainLayout from "../components/layout/MainLayout";
import {
  convertSocialLead,
  generateSocialContent,
  getSocialConsole,
  updateSocialContentStatus,
  updateSocialReplyStatus
} from "../services/socialApi";

export default function SocialPage() {
  const [data, setData] = useState({
    pending_posts: [],
    pending_replies: [],
    detected_leads: [],
    activity_logs: [],
    platform_performance: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await getSocialConsole();
      setData(res || {});
    } catch (err) {
      setError(err.message || "Failed to load social console.");
    }
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, []);

  const decidePost = async (id, status) => {
    try {
      await updateSocialContentStatus(id, status);
      await load();
    } catch (err) {
      setError(err.message || "Failed to update post status.");
    }
  };

  const decideReply = async (id, status) => {
    try {
      await updateSocialReplyStatus(id, status);
      await load();
    } catch (err) {
      setError(err.message || "Failed to update reply status.");
    }
  };

  const convertLead = async (leadId) => {
    const amount = Number(window.prompt("Confirmed revenue amount (USD):", "1200") || 0);
    if (!amount || amount <= 0) return;
    try {
      await convertSocialLead(leadId, amount);
      await load();
    } catch (err) {
      setError(err.message || "Failed to convert lead.");
    }
  };

  return (
    <MainLayout>
      <div style={{ padding: 24 }}>
        <h1>Social Growth Console</h1>
        <p style={{ color: "#94a3b8" }}>
          Human-in-the-loop only: all posts, replies, and DMs remain approval-based.
        </p>

        {error ? <p style={{ color: "#f87171" }}>{error}</p> : null}

        <button
          onClick={async () => {
            try {
              await generateSocialContent("Shipped NOVA social-to-revenue pipeline with offer and ROI tracking.");
              await load();
            } catch (err) {
              setError(err.message || "Failed to generate content suggestions.");
            }
          }}
          style={{ marginBottom: 18 }}
        >
          Generate Content Suggestions
        </button>

        {loading ? <p>Loading…</p> : null}

        <h2>Pending Posts</h2>
        {(data.pending_posts || []).map((post) => (
          <div key={post.id} style={{ border: "1px solid #1e293b", borderRadius: 8, padding: 12, marginBottom: 10 }}>
            <div><strong>{post.platform}</strong> · {post.content_type}</div>
            <div>{post.hook}</div>
            <div style={{ color: "#cbd5e1", marginTop: 6 }}>{post.body}</div>
            <div style={{ fontSize: 13, marginTop: 6 }}>CTA: {post.cta}</div>
            <div style={{ marginTop: 8, display: "flex", gap: 8 }}>
              <button onClick={() => decidePost(post.id, "approved")}>Approve</button>
              <button onClick={() => decidePost(post.id, "rejected")}>Reject</button>
              <button onClick={() => decidePost(post.id, "published")}>Mark Published</button>
            </div>
          </div>
        ))}

        <h2>Suggested Replies / DMs</h2>
        {(data.pending_replies || []).map((reply) => (
          <div key={reply.id} style={{ border: "1px solid #1e293b", borderRadius: 8, padding: 12, marginBottom: 10 }}>
            <div><strong>@{reply.username}</strong> on {reply.platform}</div>
            <div style={{ marginTop: 6 }}>{reply.suggestion}</div>
            <div style={{ marginTop: 8, display: "flex", gap: 8 }}>
              <button onClick={() => decideReply(reply.id, "approved")}>Approve</button>
              <button onClick={() => decideReply(reply.id, "rejected")}>Reject</button>
            </div>
          </div>
        ))}

        <h2>Detected Leads</h2>
        <ul>
          {(data.detected_leads || []).map((lead) => (
            <li key={lead.id}>
              {lead.platform} · @{lead.username} · {lead.intent_level} · {lead.pipeline_status || "offer_generated"}
              <button style={{ marginLeft: 8 }} onClick={() => convertLead(lead.id)}>Mark Conversion</button>
            </li>
          ))}
        </ul>

        <h2>Platform Performance</h2>
        <ul>
          {(data.platform_performance || []).map((p) => (
            <li key={p.platform}>{p.platform}: {p.published || 0} published / {p.posts || 0} total</li>
          ))}
        </ul>

        <h2>Social ROI</h2>
        <ul>
          {(data.social_roi || []).map((row) => (
            <li key={row.platform}>
              {row.platform}: leads {Math.round(row.leads || 0)} · conversions {Math.round(row.conversions || 0)} · revenue ${Number(row.revenue || 0).toFixed(2)}
            </li>
          ))}
        </ul>
      </div>
    </MainLayout>
  );
}
