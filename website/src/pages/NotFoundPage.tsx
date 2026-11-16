import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="container">
      <div className="card empty" style={{ marginTop: 48 }}>
        <span className="eyebrow">404</span>
        <h1 style={{ fontSize: "1.8rem" }}>This page does not exist</h1>
        <div className="btn-row" style={{ justifyContent: "center" }}>
          <Link className="btn btn-primary" to="/">
            Project overview
          </Link>
          <Link className="btn btn-secondary" to="/test">
            Start a test
          </Link>
        </div>
      </div>
    </div>
  );
}
