import { useEffect, useMemo, useState } from "react";
import { confirmOrder, createOrder, fetchOrderStatus } from "../services/orderApi";
import { formatCurrencyDisplay, parseCurrencyToNumber } from "../utils/formatters";
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
  const [notice, setNotice] = useState("");

  async function generatePlan() {
    if (!input.trim()) return;
    setError("");
    setNotice("");
    setLoading(true);
    setOrderStatus(null);
    setSelectedPlan("");
    setPaymentStatus("unpaid");

    try {
      const response = await createOrder(input, { source: "product_ui", payment_status: "unpaid" });
      setOrder({ ...response, payment_status: "unpaid" });
      setNotice("Plan generated. Select a tier to continue.");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function submitPayment() {
    if (!order || !selectedPlan) return;
    setLoading(true);
    setError("");
    try {
      setPaymentStatus("processing");
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setPaymentStatus("paid");
      setOrder((prev) => ({ ...prev, payment_status: "paid" }));
      await confirmOrder(order.order_id, selectedPlan);
      const status = await fetchOrderStatus(order.order_id);
      setOrderStatus(status);
      setNotice("Payment confirmed. Execution started.");
    } catch (e) {
      setPaymentStatus("unpaid");
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
          setNotice("Execution completed successfully.");
          clearInterval(timer);
        } else if (status.status === "failed") {
          setError(status?.error?.message || "Execution failed. Please try again.");
          clearInterval(timer);
        }
      } catch (e) {
        setError(e.message || "Unable to refresh order status.");
        clearInterval(timer);
      }
    }, 2500);

    return () => clearInterval(timer);
  }, [order?.order_id, paymentStatus]);

  const offers = order?.offers || [];
  const recommended = useMemo(() => String(offers[1]?.tier || offers[0]?.tier || "STANDARD").toUpperCase(), [offers]);
  const selectedOffer = offers.find((offer) => String(offer?.tier || "").toUpperCase() === selectedPlan);

  const progressSteps = [
    { key: "planning", label: "Planning", doneAt: 20 },
    { key: "building", label: "Building", doneAt: 60 },
    { key: "deploying", label: "Deploying", doneAt: 100 }
  ];

  const progress = orderStatus?.progress ?? 0;
  const result = orderStatus?.result || null;
  const websiteLink = result?.preview_url || result?.deployment_url || result?.website_url || "";

  const planPrice = parseCurrencyToNumber(selectedOffer?.estimated_price, 1200);
  const estimatedLeads = Math.max(20, Math.round(planPrice / 40));
  const potentialRevenue = estimatedLeads * 250;
  const growthPotential = potentialRevenue > 15000 ? "High" : potentialRevenue > 7000 ? "Medium" : "Early-stage";

  return (
    <main className="product-shell">
      <section className="hero-card fade-in">
        <div className="hero-top-row">
          <p className="eyebrow">USER APP</p>
          <div className="trust-chips">
            <span>AI-generated strategy</span>
            <span>Optimized for conversion</span>
          </div>
        </div>

        <h1>Describe what you want Nova to launch.</h1>
        <p className="hero-copy">From idea to paid execution with one guided conversion-focused flow.</p>

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
          {loading ? "Generating high-conversion plan..." : "Generate Plan"}
        </button>

        {error && <p className="error-text">{error}</p>}
        {notice && <p style={{ color: "#34d399", marginTop: 12 }}>{notice}</p>}
      </section>

      {loading && !order && (
        <section className="card loading-card fade-in">
          <h3>Preparing your offer stack...</h3>
          <p>Analyzing service intent, packaging options, and estimated outcomes.</p>
        </section>
      )}

      {order && (
        <section className="card-grid fade-in">
          <article className="card">
            <h3>Plan Summary</h3>
            <p><strong>Detected service:</strong> {order.service || "Unknown"}</p>
            <p><strong>Confidence:</strong> High</p>
            <p><strong>Explanation:</strong> Nova translated your request into a market-ready launch plan with clear delivery tiers.</p>
          </article>

          <article className="card">
            <h3>Pricing Options</h3>
            <div className="plan-grid">
              {offers.map((offer) => {
                const tier = String(offer.tier || "").toUpperCase();
                const isRecommended = tier === recommended;
                const isSelected = selectedPlan === tier;

                return (
                  <button
                    key={tier}
                    type="button"
                    className={`plan-card ${isRecommended ? "recommended" : ""} ${isSelected ? "selected" : ""}`}
                    onClick={() => setSelectedPlan(tier)}
                  >
                    <h4>{tier}</h4>
                    <p className="price">{formatCurrencyDisplay(offer.estimated_price, "-")}</p>
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
            <p><strong>Plan:</strong> {selectedPlan || "Choose a plan"}</p>
            <p><strong>Price:</strong> {formatCurrencyDisplay(selectedOffer?.estimated_price, "-")}</p>
            <p><strong>You get:</strong> {(PLAN_FEATURES[selectedPlan] || ["Select a plan to see deliverables"]).join(", ")}</p>
            <p><strong>Payment status:</strong> {paymentStatus}</p>

            <button
              type="button"
              className="primary-btn"
              onClick={submitPayment}
              disabled={!selectedPlan || loading || paymentStatus === "paid" || paymentStatus === "processing"}
            >
              {paymentStatus === "processing"
                ? "Processing payment..."
                : paymentStatus === "paid"
                  ? "Payment Completed"
                  : "Pay & Start Execution"}
            </button>
          </article>
        </section>
      )}

      {orderStatus && (
        <section className="card-grid fade-in">
          <article className="card">
            <h3>Execution Status</h3>
            <p><strong>Current:</strong> {orderStatus.status}</p>
            {orderStatus.status === "failed" ? (
              <p className="error-text">{orderStatus?.error?.message || "Execution failed."}</p>
            ) : null}
            <div className="step-list">
              {progressSteps.map((step) => (
                <div key={step.key} className={`step ${progress >= step.doneAt ? "done" : ""}`}>
                  {step.label}
                </div>
              ))}
            </div>
          </article>

          <article className="card">
            <h2>Your system is ready</h2>
            {websiteLink ? (
              <>
                <a className="secondary-btn" href={websiteLink} target="_blank" rel="noreferrer">Open Website Preview</a>
                <iframe title="website-preview" src={websiteLink} className="preview-frame" />
              </>
            ) : (
              <p>Website preview will appear after deployment.</p>
            )}

            <h4>Business summary</h4>
            <p>{result?.business_summary || result?.summary || "Your launch stack is configured and ready for conversion traffic."}</p>

            <h4>What you can do next</h4>
            <ul>
              <li>Connect CRM and lead notifications.</li>
              <li>Launch traffic from search/social channels.</li>
              <li>Use split tests to improve conversion rate weekly.</li>
            </ul>

            <h4>Expected results</h4>
            <p>Initial traction within 7-14 days after activation with measurable lead intent indicators.</p>

            <h4>How this will generate leads</h4>
            <p>Targeted traffic enters conversion-optimized pages, then automation qualifies and routes warm leads for follow-up.</p>
          </article>

          <article className="card value-card">
            <h3>Value Projection</h3>
            <div className="value-grid">
              <div>
                <p>Estimated leads/month</p>
                <h4>{estimatedLeads}</h4>
              </div>
              <div>
                <p>Potential revenue</p>
                <h4>${potentialRevenue.toLocaleString()}</h4>
              </div>
              <div>
                <p>Growth potential</p>
                <h4>{growthPotential}</h4>
              </div>
            </div>

            <div className="cta-row">
              <button type="button" className="primary-btn">Get full setup</button>
              <button type="button" className="secondary-btn">Run ads for this</button>
              <button type="button" className="secondary-btn">Upgrade plan</button>
            </div>
          </article>
        </section>
      )}
    </main>
  );
}
