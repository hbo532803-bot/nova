import { useEffect, useMemo, useState } from "react";
import { confirmOrder, createOrder, fetchOrderStatus } from "../services/orderApi";
import "../styles/product.css";

const SUGGESTIONS = [
  "Build a local lead-gen website for cleaning services",
  "Create a funnel + SMS workflow for auto detailing",
  "Design paid ads + landing page for a med spa launch"
];

const PLAN_FEATURES = {
  BASIC: ["Strategy outline", "Starter assets", "Basic setup"],
  STANDARD: ["Full funnel", "Automation setup", "Conversion-focused offer"],
  PREMIUM: ["Advanced funnel", "Growth experiments", "Priority optimization"]
};

export default function ProductPage() {
  const [input, setInput] = useState("");
  const [order, setOrder] = useState(null);
  const [selectedPlan, setSelectedPlan] = useState("");
  const [paymentStatus, setPaymentStatus] = useState("unpaid");
  const [orderStatus, setOrderStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function generatePlan() {
    if (!input.trim()) return;
    setError("");
    setLoading(true);
    setOrderStatus(null);
    setSelectedPlan("");
    setPaymentStatus("unpaid");

    try {
      const response = await createOrder(input, { source: "product_ui", payment_status: "unpaid" });
      setOrder({ ...response, payment_status: "unpaid" });
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function submitPayment() {
    if (!order || !selectedPlan) return;
    setLoading(true);
    try {
      setPaymentStatus("paid");
      setOrder((prev) => ({ ...prev, payment_status: "paid" }));
      await confirmOrder(order.order_id, selectedPlan);
      const status = await fetchOrderStatus(order.order_id);
      setOrderStatus(status);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!order?.order_id || paymentStatus !== "paid") return;
    const timer = setInterval(async () => {
      try {
        const status = await fetchOrderStatus(order.order_id);
        setOrderStatus(status);
        if (status.status === "completed") {
          clearInterval(timer);
        }
      } catch {
        clearInterval(timer);
      }
    }, 2500);

    return () => clearInterval(timer);
  }, [order?.order_id, paymentStatus]);

  const offers = order?.offers || [];
  const recommended = useMemo(() => offers[1]?.tier || offers[0]?.tier || "STANDARD", [offers]);

  const progressSteps = [
    { key: "planning", label: "Planning", doneAt: 20 },
    { key: "building", label: "Building", doneAt: 60 },
    { key: "deploying", label: "Deploying", doneAt: 100 }
  ];

  const progress = orderStatus?.progress ?? 0;
  const result = orderStatus?.result || null;
  const websiteLink = result?.website_url || result?.preview_url || result?.deployment_url || "";

  return (
    <main className="product-shell">
      <section className="hero-card">
        <p className="eyebrow">USER APP</p>
        <h1>Describe what you want Nova to launch.</h1>
        <p className="hero-copy">From idea to paid execution with one guided flow.</p>

        <div className="suggestions-row">
          {SUGGESTIONS.map((item) => (
            <button key={item} type="button" className="chip" onClick={() => setInput(item)}>
              {item}
            </button>
          ))}
        </div>

        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Example: Launch a lead generation website + booking flow for roofing businesses in Dallas"
          className="input-box"
        />
        <button type="button" className="primary-btn" onClick={generatePlan} disabled={loading}>
          {loading ? "Generating..." : "Generate Plan"}
        </button>
        {error && <p className="error-text">{error}</p>}
      </section>

      {order && (
        <section className="card-grid">
          <article className="card">
            <h3>Plan Summary</h3>
            <p><strong>Detected service:</strong> {order.service || "Unknown"}</p>
            <p><strong>Confidence:</strong> High</p>
            <p><strong>Explanation:</strong> Nova mapped your input to packaged service offers and generated a scoped mission.</p>
          </article>

          <article className="card">
            <h3>Pricing Options</h3>
            <div className="plan-grid">
              {offers.map((offer) => {
                const tier = String(offer.tier || "").toUpperCase();
                const isRecommended = tier === String(recommended).toUpperCase();
                const isSelected = selectedPlan === tier;
                return (
                  <button
                    key={tier}
                    type="button"
                    className={`plan-card ${isRecommended ? "recommended" : ""} ${isSelected ? "selected" : ""}`}
                    onClick={() => setSelectedPlan(tier)}
                  >
                    <h4>{tier}</h4>
                    <p className="price">${offer.estimated_price || "-"}</p>
                    <ul>
                      {(PLAN_FEATURES[tier] || []).map((f) => (
                        <li key={f}>{f}</li>
                      ))}
                    </ul>
                    {isRecommended && <span className="badge">Recommended</span>}
                  </button>
                );
              })}
            </div>
          </article>

          <article className="card">
            <h3>Payment</h3>
            <p>Selected plan: <strong>{selectedPlan || "Choose a plan"}</strong></p>
            <p>Payment status: <strong>{paymentStatus}</strong></p>
            <button
              type="button"
              className="primary-btn"
              onClick={submitPayment}
              disabled={!selectedPlan || loading || paymentStatus === "paid"}
            >
              {paymentStatus === "paid" ? "Payment Completed" : "Pay & Start Execution"}
            </button>
          </article>
        </section>
      )}

      {orderStatus && (
        <section className="card-grid">
          <article className="card">
            <h3>Execution Status</h3>
            <p><strong>Current:</strong> {orderStatus.status}</p>
            <div className="step-list">
              {progressSteps.map((step) => (
                <div key={step.key} className={`step ${progress >= step.doneAt ? "done" : ""}`}>
                  {step.label}
                </div>
              ))}
            </div>
          </article>

          <article className="card">
            <h3>Result View</h3>
            {websiteLink ? (
              <>
                <a className="secondary-btn" href={websiteLink} target="_blank" rel="noreferrer">Open Website Preview</a>
                <iframe title="website-preview" src={websiteLink} className="preview-frame" />
              </>
            ) : (
              <p>Website preview will appear after deployment.</p>
            )}
            <p><strong>Business summary:</strong> {result?.business_summary || result?.summary || "Pending result summary."}</p>
            <p><strong>Leads info:</strong> {result?.leads_info || result?.leads || "Leads pipeline details will be listed here."}</p>
          </article>
        </section>
      )}
    </main>
  );
}
