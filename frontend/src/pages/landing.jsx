import { Link } from "react-router-dom";
import "../styles/product.css";

export default function LandingPage() {
  return (
    <main className="product-shell">
      <section className="hero-card landing-card">
        <p className="eyebrow">NOVA PRODUCT LAYER</p>
        <h1>Launch your service plan in minutes.</h1>
        <p className="hero-copy">
          Convert raw ideas into a structured execution plan, select your tier, complete payment, and track fulfillment live.
        </p>
        <div className="hero-actions">
          <Link className="primary-btn" to="/product">
            Open Product App
          </Link>
          <Link className="secondary-btn" to="/login">
            Admin Login
          </Link>
        </div>
      </section>
    </main>
  );
}
