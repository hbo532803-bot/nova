import { useEffect, useState } from "react";
import MainLayout from "../components/layout/MainLayout";
import {
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

  const load = async () => {
    setLoading(true);
    const res = await getSocialConsole();
    setData(res || {});
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, []);

  const decidePost = async (id, status) => {
    await updateSocialContentStatus(id, status);
    await load();
  };

  const decideReply = async (id, status) => {
    await updateSocialReplyStatus(id, status);
    await load();
  };

  return (
    <MainLayout>
      <div style={{ padding: 24 }}>
        <h1>Social Growth Console</h1>
        <p style={{ color: "#94a3b8" }}>
          Human-in-the-loop only: all posts, replies, and DMs remain approval-based.
        </p>

        <button
          onClick={async () => {
            await generateSocialContent("Shipped NOVA market + social growth system with approval controls.");
            await load();
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
            <li key={lead.id}>{lead.platform} · @{lead.username} · {lead.intent_level}</li>
          ))}
        </ul>

        <h2>Platform Performance</h2>
        <ul>
          {(data.platform_performance || []).map((p) => (
            <li key={p.platform}>{p.platform}: {p.published || 0} published / {p.posts || 0} total</li>
          ))}
        </ul>
      </div>
    </MainLayout>
  );
}
